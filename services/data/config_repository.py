"""
配置数据访问层
负责配置文件的读取和管理
"""

import json
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from utils.logging_utils import get_logger
from utils.error_handler import FileError, ConfigError

logger = get_logger(__name__)

class BaseRepository(ABC):
    """基础Repository抽象类"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    @abstractmethod
    def get_data(self) -> Dict[str, Any]:
        """获取数据的抽象方法"""
        pass

class ConfigRepository(BaseRepository):
    """配置数据访问类"""
    
    def __init__(self, base_path: str):
        super().__init__(base_path)
        self._config_cache: Optional[Dict[str, Any]] = None
        self._abbreviations_cache: Optional[Dict[str, Any]] = None
        self._translations_cache: Optional[Dict[str, Any]] = None
    
    def get_data(self) -> Dict[str, Any]:
        """获取主配置数据，实现抽象方法"""
        return self.get_config()
    
    def get_config(self) -> Dict[str, Any]:
        """获取主配置文件"""
        if self._config_cache is None:
            config_path = os.path.join(self.base_path, 'config', 'config.json')
            self._config_cache = self._load_json_file(config_path, "主配置文件")
        return self._config_cache
    
    def get_abbreviations(self) -> Dict[str, Any]:
        """获取职业简称配置"""
        if self._abbreviations_cache is None:
            abbreviations_path = os.path.join(self.base_path, 'config', 'Abbreviations.json')
            self._abbreviations_cache = self._load_json_file(abbreviations_path, "职业简称配置")
        return self._abbreviations_cache
    
    def get_translations(self) -> Dict[str, Any]:
        """获取翻译配置"""
        if self._translations_cache is None:
            translations_path = os.path.join(self.base_path, 'config', 'en_cn_wow.json')
            self._translations_cache = self._load_json_file(translations_path, "翻译配置")
        return self._translations_cache
    
    def get_member_ids(self) -> Dict[str, Any]:
        """获取成员ID配置"""
        member_ids_path = os.path.join(self.base_path, 'config', 'member_id.txt')
        return self._load_text_file(member_ids_path, "成员ID配置")
    
    def _load_json_file(self, file_path: str, config_name: str) -> Dict[str, Any]:
        """加载JSON配置文件"""
        try:
            if not os.path.exists(file_path):
                raise FileError(f"{config_name}文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"成功加载{config_name}: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            raise ConfigError(f"{config_name}JSON格式错误: {str(e)}")
        except Exception as e:
            raise ConfigError(f"加载{config_name}失败: {str(e)}")
    
    def _load_text_file(self, file_path: str, config_name: str) -> Dict[str, Any]:
        """加载文本配置文件"""
        try:
            if not os.path.exists(file_path):
                raise FileError(f"{config_name}文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 将文本内容按行分割并转换为字典
            lines = content.split('\n')
            result = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释
                    if '=' in line:
                        key, value = line.split('=', 1)
                        result[key.strip()] = value.strip()
                    else:
                        result[line] = True
            
            logger.debug(f"成功加载{config_name}: {file_path}")
            return result
            
        except Exception as e:
            raise ConfigError(f"加载{config_name}失败: {str(e)}")
    
    def reload_config(self):
        """重新加载所有配置"""
        logger.info("重新加载所有配置文件")
        self._config_cache = None
        self._abbreviations_cache = None
        self._translations_cache = None
    
    def get_bot_config(self) -> Dict[str, Any]:
        """获取机器人相关配置"""
        config = self.get_config()
        return {
            'openai_api2d_url': config.get('openai_api2d_url'),
            'openai_api2d_api_key': config.get('openai_api2d_api_key'),
            'bot_token': config.get('bot_token'),
            'verify_token': config.get('verify_token'),
            'encrypt_key': config.get('encrypt_key')
        }
    
    def get_channel_config(self) -> Dict[str, Any]:
        """获取频道相关配置"""
        config = self.get_config()
        return {
            'admin_channels': config.get('admin_channels', [])
        }
    
    def get_feature_config(self) -> Dict[str, Any]:
        """获取功能开关配置"""
        config = self.get_config()
        return {
            'enable_talent_query': config.get('enable_talent_query', True),
            'enable_ai_chat': config.get('enable_ai_chat', True),
            'enable_random_reply': config.get('enable_random_reply', True)
        }
