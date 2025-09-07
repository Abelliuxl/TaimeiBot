"""
玩家数据访问层
负责玩家相关数据的读取和管理
"""

import json
import os
from typing import Dict, Any, List, Optional
from .config_repository import BaseRepository
from utils.logging_utils import get_logger
from utils.error_handler import FileError, ConfigError

logger = get_logger(__name__)

class PlayerRepository(BaseRepository):
    """玩家数据访问类"""
    
    def __init__(self, base_path: str):
        super().__init__(base_path)
        self._member_data_cache: Optional[Dict[str, Any]] = None
        self._player_info_cache: Optional[List[Dict[str, Any]]] = None
    
    def get_data(self) -> Dict[str, Any]:
        """实现基类的抽象方法，返回所有玩家数据"""
        return {
            'member_data': self.get_member_data(),
            'player_info': self.get_player_info()
        }
    
    def get_member_data(self) -> Dict[str, Any]:
        """获取成员数据"""
        if self._member_data_cache is None:
            member_data_path = os.path.join(self.base_path, 'config', 'member.py')
            self._member_data_cache = self._load_member_data_file(member_data_path)
        return self._member_data_cache
    
    def get_player_info(self) -> List[Dict[str, Any]]:
        """获取玩家信息数据（从raider_data目录）"""
        if self._player_info_cache is None:
            player_info_path = os.path.join(self.base_path, '..', 'raider_data', 'player_info.json')
            self._player_info_cache = self._load_player_info_file(player_info_path)
        return self._player_info_cache
    
    def _load_member_data_file(self, file_path: str) -> Dict[str, Any]:
        """加载成员数据文件（Python格式）"""
        try:
            if not os.path.exists(file_path):
                raise FileError(f"成员数据文件不存在: {file_path}")
            
            # 使用exec执行Python文件，获取其中的变量
            local_vars = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                exec(f.read(), {}, local_vars)
            
            # 过滤出我们需要的变量
            result = {}
            for key, value in local_vars.items():
                if not key.startswith('__') and not callable(value):
                    result[key] = value
            
            logger.debug(f"成功加载成员数据: {file_path}")
            return result
            
        except Exception as e:
            raise ConfigError(f"加载成员数据失败: {str(e)}")
    
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
    
    def get_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据玩家名称查找玩家"""
        player_info = self.get_player_info()
        for player in player_info:
            if player.get("name") == name:
                return player
        return None
    
    def get_players_by_realm(self, realm: str) -> List[Dict[str, Any]]:
        """根据服务器查找玩家"""
        player_info = self.get_player_info()
        return [player for player in player_info if player.get("realm") == realm]
    
    def get_players_by_region(self, region: str) -> List[Dict[str, Any]]:
        """根据地区查找玩家"""
        player_info = self.get_player_info()
        return [player for player in player_info if player.get("region") == region]
    
    def get_players_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        """根据职业查找玩家"""
        player_info = self.get_player_info()
        return [player for player in player_info if player.get("class") == class_name]
    
    def get_players_by_class_spec(self, class_name: str, spec: str) -> List[Dict[str, Any]]:
        """根据职业和专精查找玩家"""
        player_info = self.get_player_info()
        return [
            player for player in player_info
            if player.get("class") == class_name and player.get("spec") == spec
        ]
    
    def get_member_by_id(self, member_id: str) -> Optional[Dict[str, Any]]:
        """根据成员ID查找成员"""
        member_data = self.get_member_data()
        return member_data.get(member_id)
    
    def get_all_member_ids(self) -> List[str]:
        """获取所有成员ID"""
        member_data = self.get_member_data()
        return list(member_data.keys())
    
    def get_member_names(self) -> List[str]:
        """获取所有成员名称"""
        member_data = self.get_member_data()
        return [member.get('name', '') for member in member_data.values()]
    
    def search_players(self, query: str) -> List[Dict[str, Any]]:
        """搜索玩家（支持名称、职业、专精、服务器）"""
        player_info = self.get_player_info()
        query = query.lower()
        results = []
        
        for player in player_info:
            # 检查名称
            if query in player.get("name", "").lower():
                results.append(player)
                continue
            
            # 检查职业
            if query in player.get("class", "").lower():
                results.append(player)
                continue
            
            # 检查专精
            if query in player.get("spec", "").lower():
                results.append(player)
                continue
            
            # 检查服务器
            if query in player.get("realm", "").lower():
                results.append(player)
                continue
        
        return results
    
    def get_unique_realms(self) -> List[str]:
        """获取所有唯一的服务器名称"""
        player_info = self.get_player_info()
        realms = set()
        for player in player_info:
            realms.add(player.get("realm", ""))
        return sorted(list(realms))
    
    def get_unique_regions(self) -> List[str]:
        """获取所有唯一的地区"""
        player_info = self.get_player_info()
        regions = set()
        for player in player_info:
            regions.add(player.get("region", ""))
        return sorted(list(regions))
    
    def get_player_statistics(self) -> Dict[str, Any]:
        """获取玩家统计信息"""
        player_info = self.get_player_info()
        
        # 基础统计
        total_players = len(player_info)
        
        # 按职业统计
        class_stats = {}
        # 按专精统计
        spec_stats = {}
        # 按地区统计
        region_stats = {}
        # 按服务器统计
        realm_stats = {}
        
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
            
            # 服务器统计
            realm = player.get("realm")
            realm_stats[realm] = realm_stats.get(realm, 0) + 1
        
        return {
            'total_players': total_players,
            'class_distribution': class_stats,
            'spec_distribution': spec_stats,
            'region_distribution': region_stats,
            'realm_distribution': realm_stats,
            'unique_realms': len(realm_stats),
            'unique_regions': len(region_stats)
        }
    
    def reload_player_data(self):
        """重新加载玩家数据"""
        logger.info("重新加载玩家数据")
        self._member_data_cache = None
        self._player_info_cache = None
    
    def validate_player_data_integrity(self) -> Dict[str, Any]:
        """验证玩家数据完整性"""
        player_info = self.get_player_info()
        
        issues = []
        warnings = []
        
        for i, player in enumerate(player_info):
            # 检查必需字段
            required_fields = ['name', 'realm', 'region', 'class', 'spec']
            missing_fields = [field for field in required_fields if field not in player]
            
            if missing_fields:
                issues.append(f"玩家 {i}: 缺少字段 {missing_fields}")
            
            # 检查空值
            empty_fields = [field for field in required_fields if not player.get(field)]
            if empty_fields:
                warnings.append(f"玩家 {player.get('name', i)}: 字段为空 {empty_fields}")
            
            # 检查数据格式
            if not isinstance(player.get('name'), str):
                issues.append(f"玩家 {i}: name字段类型错误")
            
            if not isinstance(player.get('realm'), str):
                issues.append(f"玩家 {i}: realm字段类型错误")
        
        return {
            'total_players': len(player_info),
            'issues': issues,
            'warnings': warnings,
            'data_integrity_score': max(0, 100 - len(issues) * 10 - len(warnings) * 2)
        }
