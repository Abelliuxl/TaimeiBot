"""
安全配置模块
提供敏感信息加密和环境变量支持
"""

import os
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
from utils.logging_utils import get_logger
from utils.error_handler import ConfigError, ValidationError

logger = get_logger(__name__)

class SecurityConfig:
    """安全配置管理类"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化安全配置
        
        Args:
            encryption_key: 加密密钥，如果未提供将从环境变量获取
        """
        self.encryption_key = encryption_key or os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            # 如果没有提供加密密钥，生成一个警告
            logger.warning("未提供加密密钥，敏感信息将以明文存储")
            self.fernet = None
        else:
            # 确保密钥是32字节的base64编码格式
            if len(self.encryption_key) != 44:  # 32字节base64编码后是44字符
                # 如果密钥长度不对，尝试从密码派生
                self.encryption_key = self._derive_key(self.encryption_key)
            
            try:
                self.fernet = Fernet(self.encryption_key.encode())
            except Exception as e:
                raise ConfigError(f"初始化加密模块失败: {str(e)}")
    
    def _derive_key(self, password: str) -> str:
        """
        从密码派生加密密钥
        
        Args:
            password: 密码
            
        Returns:
            base64编码的加密密钥
        """
        password_bytes = password.encode()
        salt = b'taimeibot_salt'  # 固定盐值，实际应用中应该使用随机盐值
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key.decode()
    
    def encrypt(self, data: str) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            加密后的base64字符串
        """
        if not self.fernet:
            # 如果没有加密功能，返回原始数据
            logger.warning("加密功能未启用，返回明文数据")
            return data
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"加密数据失败: {str(e)}")
            raise ConfigError(f"加密数据失败: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的base64字符串
            
        Returns:
            解密后的原始数据
        """
        if not self.fernet:
            # 如果没有加密功能，返回原始数据
            logger.warning("解密功能未启用，返回原始数据")
            return encrypted_data
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"解密数据失败: {str(e)}")
            raise ConfigError(f"解密数据失败: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        加密字典中的敏感字段
        
        Args:
            data: 要加密的字典
            
        Returns:
            加密后的字典
        """
        encrypted_data = data.copy()
        
        # 敏感字段列表
        sensitive_fields = [
            'api_key', 'secret', 'password', 'token', 'key',
            'llm_api_key', 'bot_token', 'encrypt_key'
        ]
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解密字典中的敏感字段
        
        Args:
            data: 要解密的字典
            
        Returns:
            解密后的字典
        """
        decrypted_data = data.copy()
        
        # 敏感字段列表
        sensitive_fields = [
            'api_key', 'secret', 'password', 'token', 'key',
            'llm_api_key', 'bot_token', 'encrypt_key'
        ]
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
                except Exception as e:
                    logger.warning(f"解密字段 {field} 失败: {str(e)}")
                    # 保持原值不解密
        
        return decrypted_data
    
    def get_env_var(self, key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """
        安全获取环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            required: 是否必需
            
        Returns:
            环境变量值
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ConfigError(f"必需的环境变量 {key} 未设置")
        
        return value
    
    def load_config_from_env(self, config_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        从环境变量加载配置
        
        Args:
            config_template: 配置模板
            
        Returns:
            加载的配置字典
        """
        config = config_template.copy()
        
        def _load_from_env(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    env_key = f"TAIMEI_{current_path.upper().replace('.', '_')}"
                    
                    if isinstance(value, dict):
                        obj[key] = _load_from_env(value, current_path)
                    elif isinstance(value, (str, int, float, bool)):
                        env_value = os.getenv(env_key)
                        if env_value is not None:
                            # 尝试转换类型
                            if isinstance(value, bool):
                                obj[key] = env_value.lower() in ('true', '1', 'yes', 'on')
                            elif isinstance(value, int):
                                obj[key] = int(env_value)
                            elif isinstance(value, float):
                                obj[key] = float(env_value)
                            else:
                                obj[key] = env_value
                    elif isinstance(value, list):
                        env_value = os.getenv(env_key)
                        if env_value is not None:
                            # 简单的列表解析（逗号分隔）
                            obj[key] = [item.strip() for item in env_value.split(',') if item.strip()]
            
            return obj
        
        return _load_from_env(config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置的有效性
        
        Args:
            config: 配置字典
            
        Returns:
            配置是否有效
        """
        required_fields = [
            'llm_api_url',
            'llm_api_key',
            'llm_model',
            'bot_token',
            'verify_token',
            'encrypt_key'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(f"配置缺少必需字段: {', '.join(missing_fields)}")
        
        # 验证URL格式
        if not config['llm_api_url'].startswith(('http://', 'https://')):
            raise ValidationError("llm_api_url 必须是有效的URL")
        
        # 验证token长度
        if len(config['bot_token']) < 10:
            raise ValidationError("bot_token 长度不足")
        
        if len(config['verify_token']) < 5:
            raise ValidationError("verify_token 长度不足")
        
        return True
    
    def mask_sensitive_data(self, data: str, mask_char: str = '*') -> str:
        """
        屏蔽敏感数据用于日志记录
        
        Args:
            data: 原始数据
            mask_char: 屏蔽字符
            
        Returns:
            屏蔽后的数据
        """
        # 敏感信息模式
        sensitive_patterns = [
            r'sk-[A-Za-z0-9]{48}',  # OpenAI API key
            r'ghp_[A-Za-z0-9]{36}',  # GitHub token
            r'xox[bap]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{32}',  # Slack token
            r'[A-Za-z0-9/_-]{20,}',  # 一般的token/key模式
        ]
        
        masked_data = data
        for pattern in sensitive_patterns:
            import re
            matches = re.findall(pattern, masked_data)
            for match in matches:
                if len(match) > 8:
                    # 保留前4位和后4位，中间用*替代
                    masked = match[:4] + mask_char * (len(match) - 8) + match[-4:]
                    masked_data = masked_data.replace(match, masked)
        
        return masked_data
    
    def generate_encryption_key(self) -> str:
        """
        生成新的加密密钥
        
        Returns:
            base64编码的加密密钥
        """
        key = Fernet.generate_key()
        return key.decode()
    
    def rotate_encryption_key(self, old_key: str, new_key: str, encrypted_data: str) -> str:
        """
        轮换加密密钥
        
        Args:
            old_key: 旧密钥
            new_key: 新密钥
            encrypted_data: 用旧密钥加密的数据
            
        Returns:
            用新密钥加密的数据
        """
        try:
            # 用旧密钥解密
            old_fernet = Fernet(old_key.encode())
            decrypted_data = old_fernet.decrypt(base64.b64decode(encrypted_data.encode()))
            
            # 用新密钥加密
            new_fernet = Fernet(new_key.encode())
            reencrypted_data = new_fernet.encrypt(decrypted_data)
            
            return base64.b64encode(reencrypted_data).decode()
        except Exception as e:
            raise ConfigError(f"轮换加密密钥失败: {str(e)}")

# 全局安全配置实例
_security_config: Optional[SecurityConfig] = None

def get_security_config(encryption_key: Optional[str] = None) -> SecurityConfig:
    """获取安全配置实例"""
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig(encryption_key)
    return _security_config

def initialize_security_config(encryption_key: Optional[str] = None):
    """初始化安全配置"""
    global _security_config
    _security_config = SecurityConfig(encryption_key)
    logger.info("安全配置模块初始化完成")
