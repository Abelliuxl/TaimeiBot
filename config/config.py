import json
import os
from typing import Dict, Any, Optional
from utils.logging_utils import get_logger
from utils.security_config import get_security_config, SecurityConfig
from utils.error_handler import ConfigError, ValidationError, log_error
from .constants import *

logger = get_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._security_config: Optional[SecurityConfig] = None
        self._config_template = self._get_config_template()
    
    def _get_config_template(self) -> Dict[str, Any]:
        """获取配置模板"""
        return {
            "llm_api_url": DEFAULT_LLM_API_URL,
            "llm_api_key": "",
            "llm_model": "",
            "bot_token": "",
            "verify_token": "",
            "encrypt_key": "",
            "bot_id": DEFAULT_BOT_ID,
            "admin_channels": DEFAULT_ADMIN_CHANNELS,
            "webhook_port": DEFAULT_WEBHOOK_PORT,
            "using_ws": DEFAULT_USING_WS,
            "enable_talent_query": DEFAULT_ENABLE_TALENT_QUERY,
            "enable_ai_chat": DEFAULT_ENABLE_AI_CHAT,
            "enable_random_reply": DEFAULT_ENABLE_RANDOM_REPLY
        }
    
    def initialize(self, encryption_key: Optional[str] = None) -> 'ConfigManager':
        """初始化配置管理器"""
        try:
            # 初始化安全配置
            self._security_config = get_security_config(encryption_key)
            
            # 加载配置
            self._config = self._load_config()
            
            logger.info("配置管理器初始化完成")
            return self
            
        except Exception as e:
            log_error(logger, e, {'function': 'initialize'})
            raise ConfigError(f"配置管理器初始化失败: {str(e)}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config = self._config_template.copy()
        
        try:
            # 1. 首先从config.json文件加载基础配置
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.debug("从config.json加载配置")
            
            # 2. 从环境变量覆盖配置
            config = self._security_config.load_config_from_env(config)
            logger.debug("从环境变量加载配置")
            
            # 3. 解密敏感字段
            config = self._security_config.decrypt_dict(config)
            logger.debug("解密敏感配置字段")
            
            # 4. 验证配置
            self._security_config.validate_config(config)
            logger.debug("配置验证通过")
            
            return config
            
        except FileNotFoundError:
            logger.warning("config.json文件不存在，将使用默认配置和环境变量")
            # 如果文件不存在，继续使用环境变量
            config = self._security_config.load_config_from_env(config)
            config = self._security_config.decrypt_dict(config)
            self._security_config.validate_config(config)
            return config
            
        except json.JSONDecodeError as e:
            log_error(logger, e, {'function': '_load_config'})
            raise ConfigError(f"配置文件JSON格式错误: {str(e)}")
            
        except Exception as e:
            log_error(logger, e, {'function': '_load_config'})
            raise ConfigError(f"加载配置失败: {str(e)}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        if self._config is None:
            raise ConfigError("配置管理器未初始化")
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if self._config is None:
            raise ConfigError("配置管理器未初始化")
        return self._config.get(key, default)
    
    def get_bot_config(self) -> Dict[str, Any]:
        """获取机器人相关配置"""
        return {
            'llm_api_url': self.get('llm_api_url'),
            'llm_api_key': self.get('llm_api_key'),
            'llm_model': self.get('llm_model'),
            'bot_token': self.get('bot_token'),
            'verify_token': self.get('verify_token'),
            'encrypt_key': self.get('encrypt_key')
        }
    
    def get_channel_config(self) -> Dict[str, Any]:
        """获取频道相关配置"""
        return {
            'translation_channels': self.get('translation_channels', []),
            'admin_channels': self.get('admin_channels', [])
        }
    
    def get_feature_config(self) -> Dict[str, Any]:
        """获取功能开关配置"""
        return {
            'enable_translation': self.get('enable_translation', True),
            'enable_talent_query': self.get('enable_talent_query', True),
            'enable_ai_chat': self.get('enable_ai_chat', True),
            'enable_random_reply': self.get('enable_random_reply', True)
        }
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置到文件"""
        try:
            if config is None:
                config = self._config
            
            if config is None:
                raise ConfigError("没有配置可保存")
            
            # 加密敏感字段
            encrypted_config = self._security_config.encrypt_dict(config)
            
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(encrypted_config, f, indent=2, ensure_ascii=False)
            
            logger.info("配置保存成功")
            return True
            
        except Exception as e:
            log_error(logger, e, {'function': 'save_config'})
            raise ConfigError(f"保存配置失败: {str(e)}")
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            self._config = self._load_config()
            logger.info("配置重新加载成功")
            return True
        except Exception as e:
            log_error(logger, e, {'function': 'reload_config'})
            raise ConfigError(f"重新加载配置失败: {str(e)}")
    
    def update_config(self, key: str, value: Any) -> bool:
        """更新配置项"""
        try:
            if self._config is None:
                raise ConfigError("配置管理器未初始化")
            
            self._config[key] = value
            logger.info(f"配置项 {key} 更新成功")
            return True
        except Exception as e:
            log_error(logger, e, {'function': 'update_config', 'key': key})
            raise ConfigError(f"更新配置项失败: {str(e)}")
    
    def get_security_config(self) -> SecurityConfig:
        """获取安全配置实例"""
        if self._security_config is None:
            raise ConfigError("安全配置未初始化")
        return self._security_config
    
    def mask_config_for_logging(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """为日志记录屏蔽敏感配置信息"""
        masked_config = config.copy()
        
        # 屏蔽敏感字段
        sensitive_fields = [
            'llm_api_key', 'bot_token', 'verify_token', 'encrypt_key'
        ]
        
        for field in sensitive_fields:
            if field in masked_config and masked_config[field]:
                masked_config[field] = self._security_config.mask_sensitive_data(
                    str(masked_config[field])
                )
        
        return masked_config

# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None

def get_config_manager(encryption_key: Optional[str] = None) -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.initialize(encryption_key)
    return _config_manager

def initialize_config(encryption_key: Optional[str] = None) -> ConfigManager:
    """初始化配置管理器"""
    global _config_manager
    _config_manager = ConfigManager()
    _config_manager.initialize(encryption_key)
    logger.info("配置模块初始化完成")
    return _config_manager

# 为了向后兼容，保留全局变量
_config: Optional[Dict[str, Any]] = None

def load_config() -> Dict[str, Any]:
    """加载配置（向后兼容函数）"""
    global _config
    if _config is None:
        config_manager = get_config_manager()
        _config = config_manager.get_config()
    return _config

# 向后兼容的全局变量
config = load_config()
BOT_TOKEN = config.get("bot_token")
VERIFY_TOKEN = config.get("verify_token")
ENCRYPT_TOKEN = config.get("encrypt_key")
