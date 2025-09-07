import aiohttp
import os
from typing import Optional, Dict, Any
from utils.logging_utils import get_logger
from utils.error_handler import APIError, NetworkError, log_error
from utils.retry_decorator import retry, get_default_retry_config
from utils.cache_decorator import raider_cache

logger = get_logger(__name__)

class RaiderService:
    """Raider.io API服务类"""
    
    def __init__(self, config_manager):
        """
        初始化Raider服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.base_url = 'https://raider.io/api/v1'
        
    @retry(**get_default_retry_config().__dict__)
    async def _make_api_request(self, session: aiohttp.ClientSession, url: str, params: dict) -> dict:
        """发送API请求的辅助函数"""
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                raise APIError(f"API资源未找到: {url}", status_code=response.status)
            elif response.status == 429:
                raise APIError(f"API请求过于频繁: {url}", status_code=response.status)
            elif response.status >= 500:
                raise APIError(f"API服务器错误: {url}", status_code=response.status)
            else:
                raise APIError(f"API请求失败: {url}", status_code=response.status)
    
    async def _get_data_repositories(self):
        """获取数据仓库实例"""
        try:
            # 获取当前文件所在目录的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)  # 获取项目根目录
            
            # 导入数据仓库
            from services.data import ConfigRepository, GameDataRepository
            
            # 初始化数据仓库
            config_repo = ConfigRepository(base_dir)
            game_data_repo = GameDataRepository(base_dir)
            
            return config_repo, game_data_repo
            
        except Exception as e:
            log_error(logger, e, {'function': '_get_data_repositories'})
            raise
    
    def _translate_text(self, text: str, translation_data: Dict[str, str]) -> str:
        """翻译文本"""
        return translation_data.get(text.lower(), text)
    
    async def _get_current_season(self, session: aiohttp.ClientSession) -> str:
        """从本地配置文件读取当前赛季信息"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)
            
            # 读取 raider_data 目录中的赛季配置文件
            season_config_path = os.path.join(base_dir, '..', 'raider_data', 'season_config.json')
            
            if not os.path.exists(season_config_path):
                logger.warning(f"赛季配置文件不存在: {season_config_path}")
                return "season-tww-3"
            
            with open(season_config_path, 'r', encoding='utf-8') as f:
                season_config = json.load(f)
            
            current_season = season_config.get('season')
            
            if not current_season:
                logger.warning("赛季配置文件中未找到赛季信息")
                return "season-tww-3"
            
            logger.info(f"从本地配置文件读取到当前赛季: {current_season}")
            return current_season
            
        except Exception as e:
            logger.warning(f"读取赛季配置文件失败: {str(e)}")
            return "season-tww-3"
    
    @raider_cache(ttl=1800, key_prefix="talent_loadouts")
    async def fetch_talent_loadouts(self, spec_simple: str) -> Optional[str]:
        """
        获取天赋配置信息
        
        Args:
            spec_simple: 职业专精简称
            
        Returns:
            格式化的天赋信息字符串，如果失败返回None
        """
        try:
            # 获取数据仓库
            config_repo, game_data_repo = await self._get_data_repositories()

            # 查询目标职业和专精
            class_spec_result = game_data_repo.find_class_spec_by_abbreviation(spec_simple)
            
            if class_spec_result is None:
                logger.warning(f"未找到匹配的职业和专精: {spec_simple}")
                return None
            
            target_class, target_spec = class_spec_result
            logger.info(f"查询 {target_class} {target_spec} 的天赋配置")

            # 获取匹配的玩家信息
            matching_players = game_data_repo.find_players_by_class_spec(target_class, target_spec)

        except Exception as e:
            log_error(logger, e, {'function': 'fetch_talent_loadouts', 'spec_simple': spec_simple})
            return None

        # 存储提取的结果
        result_list = []

        # 创建aiohttp会话
        async with aiohttp.ClientSession() as session:
            # 遍历匹配的角色信息
            for info in matching_players:
                region = info.get("region")
                realm = info.get("realm")
                name = info.get("name")

                if not all([region, realm, name]):
                    logger.warning(f"角色信息不完整: {info}")
                    continue

                # 构建API请求
                url = f'{self.base_url}/characters/profile'
                params = {
                    'region': region,
                    'realm': realm,
                    'name': name,
                    'fields': 'talents'
                }

                try:
                    logger.debug(f"请求角色 {name} 的天赋信息")
                    # 发送异步API请求
                    result = await self._make_api_request(session, url, params)

                    # 提取所需字段
                    talent_loadout = result.get("talentLoadout", {})
                    loadout_text = talent_loadout.get("loadout_text", "")

                    extracted_result = {
                        "name": result.get("name"),
                        "race": result.get("race"),
                        "faction": result.get("faction"),
                        "region": region,
                        "realm": realm,
                        "loadout_text": loadout_text
                    }

                    # 添加到结果列表
                    result_list.append(extracted_result)
                    
                except (APIError, NetworkError) as e:
                    logger.warning(f"角色 {name} 的API请求失败: {str(e)}")
                    continue
                except Exception as e:
                    log_error(logger, e, {'function': 'fetch_talent_loadouts', 'character': name})
                    continue

        if not result_list:
            logger.warning(f"未找到 {target_class} {target_spec} 的有效角色数据")
            return None

        # 获取翻译数据
        try:
            translation_data = config_repo.get_translations()
        except Exception as e:
            log_error(logger, e, {'function': 'fetch_talent_loadouts', 'step': 'get_translations'})
            return None

        # 将结果整理为字符串格式
        result_string = "## raider.io上 {} {} 的天赋如下：\n\n".format(
            self._translate_text(target_spec, translation_data), 
            self._translate_text(target_class, translation_data)
        )

        for index, result in enumerate(result_list, start=1):
            result_string += "{}. **角色名**：{}，**种族**：{}，**阵营**：{}，**地区**：{}\n".format(
                index, 
                self._translate_text(result["name"], translation_data), 
                self._translate_text(result["race"], translation_data), 
                self._translate_text(result["faction"], translation_data), 
                result["region"]
            )
            result_string += "**天赋代码**：{}\n\n".format(result["loadout_text"])
        
        # 在最后增加一条：详细数据访问url
        # 动态获取当前赛季信息
        try:
            current_season = await self._get_current_season(session)
            detailed_url = f"https://raider.io/mythic-plus-spec-rankings/{current_season}/world/{target_class}/{target_spec}"
        except Exception as e:
            logger.warning(f"获取当前赛季失败，使用默认赛季: {str(e)}")
            # 使用默认赛季作为回退
            current_season = "season-tww-3"  # 根据您提到的，当前应该是 season-tww-3
            detailed_url = f"https://raider.io/mythic-plus-spec-rankings/{current_season}/world/{target_class}/{target_spec}"
        
        result_string += "详细数据访问Raider.io官网：{}\n".format(detailed_url)
        
        logger.info(f"成功获取 {len(result_list)} 个角色的天赋信息")
        return result_string

# 为了向后兼容，保留全局函数
async def fetch_talent_loadouts(spec_simple: str) -> Optional[str]:
    """
    获取天赋配置信息（向后兼容函数）
    
    Args:
        spec_simple: 职业专精简称
        
    Returns:
        格式化的天赋信息字符串，如果失败返回None
    """
    try:
        from services.container import get_container
        container = get_container()
        raider_service = await container.get_async('raider_service')
        return await raider_service.fetch_talent_loadouts(spec_simple)
    except Exception as e:
        log_error(logger, e, {'function': 'fetch_talent_loadouts_compatibility'})
        return None
