"""
游戏数据访问层
负责游戏相关数据的读取和管理
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from .config_repository import BaseRepository
from utils.logging_utils import get_logger
from utils.error_handler import FileError, ConfigError

logger = get_logger(__name__)

class GameDataRepository(BaseRepository):
    """游戏数据访问类"""
    
    def __init__(self, base_path: str):
        super().__init__(base_path)
        self._class_spec_cache: Optional[Dict[str, Any]] = None
        self._player_info_cache: Optional[List[Dict[str, Any]]] = None
    
    def get_data(self) -> Dict[str, Any]:
        """实现基类的抽象方法，返回所有游戏数据"""
        return {
            'class_spec': self.get_class_spec_data(),
            'player_info': self.get_player_info()
        }
    
    def get_class_spec_data(self) -> Dict[str, Any]:
        """获取职业专精数据"""
        if self._class_spec_cache is None:
            class_spec_path = os.path.join(self.base_path, 'config', 'class_spec_abbre.txt')
            self._class_spec_cache = self._load_class_spec_file(class_spec_path)
        return self._class_spec_cache
    
    def get_player_info(self) -> List[Dict[str, Any]]:
        """获取玩家信息数据"""
        if self._player_info_cache is None:
            player_info_path = os.path.join(self.base_path, '..', 'raider_data', 'player_info.json')
            self._player_info_cache = self._load_player_info_file(player_info_path)
        return self._player_info_cache
    
    def _load_class_spec_file(self, file_path: str) -> Dict[str, Any]:
        """加载职业专精配置文件"""
        try:
            if not os.path.exists(file_path):
                raise FileError(f"职业专精配置文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 解析YAML格式的职业专精数据
            import yaml
            data = yaml.safe_load(content)
            
            if not isinstance(data, dict):
                raise ConfigError("职业专精配置文件格式错误：应该是字典格式")
            
            # 转换数据格式为内部使用的格式
            result = {}
            for class_name, specs in data.items():
                if isinstance(specs, dict):
                    result[class_name] = {}
                    for spec, abbreviations in specs.items():
                        if isinstance(abbreviations, list):
                            result[class_name][spec] = abbreviations
                        else:
                            result[class_name][spec] = [abbreviations] if abbreviations else []
            
            logger.debug(f"成功加载职业专精数据: {len(result)} 个职业")
            return result
            
        except ImportError:
            raise ConfigError("缺少YAML解析库，请安装pyyaml：pip install pyyaml")
        except Exception as e:
            raise ConfigError(f"加载职业专精配置失败: {str(e)}")
    
    def _load_player_info_file(self, file_path: str) -> List[Dict[str, Any]]:
        """加载玩家信息文件"""
        try:
            if not os.path.exists(file_path):
                raise FileError(f"玩家信息文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ConfigError("玩家信息文件格式错误：应该是数组格式")
            
            # 验证数据格式
            valid_players = []
            for player in data:
                if self._validate_player_info(player):
                    valid_players.append(player)
                else:
                    logger.warning(f"玩家信息格式不正确，已跳过: {player}")
            
            logger.debug(f"成功加载玩家信息: {len(valid_players)} 个有效玩家")
            return valid_players
            
        except json.JSONDecodeError as e:
            raise ConfigError(f"玩家信息文件JSON格式错误: {str(e)}")
        except Exception as e:
            raise ConfigError(f"加载玩家信息失败: {str(e)}")
    
    def _validate_player_info(self, player: Dict[str, Any]) -> bool:
        """验证玩家信息格式"""
        required_fields = ['name', 'realm', 'region', 'class', 'spec']
        return all(field in player for field in required_fields)
    
    def find_players_by_class_spec(self, target_class: str, target_spec: str) -> List[Dict[str, Any]]:
        """根据职业和专精查找玩家"""
        player_info = self.get_player_info()
        
        # 现在target_class和target_spec直接是英文键，可以直接匹配
        logger.debug(f"查找玩家: {target_class} {target_spec}")
        
        return [
            player for player in player_info
            if player.get("class") == target_class and player.get("spec") == target_spec
        ]
    
    def find_class_spec_by_abbreviation(self, abbreviation: str) -> Optional[Tuple[str, str]]:
        """根据简称查找职业和专精"""
        try:
            from .config_repository import ConfigRepository
            config_repo = ConfigRepository(self.base_path)
            abbreviations = config_repo.get_abbreviations()
            
            abbreviation = abbreviation.lower()
            
            # 直接遍历Abbreviations.json查找匹配的简称
            for en_class, specs in abbreviations.items():
                for en_spec, cn_abbreviations in specs.items():
                    if abbreviation in [abbr.lower() for abbr in cn_abbreviations]:
                        return en_class, en_spec
            
        except Exception as e:
            logger.warning(f"从Abbreviations.json查找失败: {str(e)}")
            
        # 如果Abbreviations.json查找失败，回退到原来的class_spec_abbre.txt
        class_spec_data = self.get_class_spec_data()
        for class_name, specs in class_spec_data.items():
            for spec, abbreviations in specs.items():
                if abbreviation in [abbr.lower() for abbr in abbreviations]:
                    return class_name, spec
        
        return None
    
    def get_all_classes(self) -> List[str]:
        """获取所有职业列表"""
        class_spec_data = self.get_class_spec_data()
        return list(class_spec_data.keys())
    
    def get_specs_by_class(self, class_name: str) -> List[str]:
        """获取指定职业的所有专精"""
        class_spec_data = self.get_class_spec_data()
        return list(class_spec_data.get(class_name, {}).keys())
    
    def get_abbreviations_by_class_spec(self, class_name: str, spec: str) -> List[str]:
        """获取指定职业专精的所有简称"""
        class_spec_data = self.get_class_spec_data()
        return class_spec_data.get(class_name, {}).get(spec, [])
    
    def reload_game_data(self):
        """重新加载游戏数据"""
        logger.info("重新加载游戏数据")
        self._class_spec_cache = None
        self._player_info_cache = None
    
    def get_player_statistics(self) -> Dict[str, Any]:
        """获取玩家统计信息"""
        player_info = self.get_player_info()
        
        # 按职业统计
        class_stats = {}
        # 按专精统计
        spec_stats = {}
        # 按地区统计
        region_stats = {}
        
        for player in player_info:
            # 职业统计
            class_name = player.get("class")
            class_stats[class_name] = class_stats.get(class_name, 0) + 1
            
            # 专精统计
            spec = player.get("spec")
            spec_key = f"{class_name}-{spec}"
            spec_stats[spec_key] = spec_stats.get(spec_key, 0) + 1
            
            # 地区统计
            region = player.get("region")
            region_stats[region] = region_stats.get(region, 0) + 1
        
        return {
            'total_players': len(player_info),
            'class_distribution': class_stats,
            'spec_distribution': spec_stats,
            'region_distribution': region_stats
        }
