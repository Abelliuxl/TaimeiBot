"""
基础错误类定义
"""

from typing import Optional
from enum import Enum

class ErrorType(Enum):
    """错误类型枚举"""
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"
    VALIDATION_ERROR = "validation_error"
    FILE_ERROR = "file_error"
    UNKNOWN_ERROR = "unknown_error"

class TaimeiBotError(Exception):
    """TaimeiBot基础异常类"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 original_error: Optional[Exception] = None, 
                 user_message: Optional[str] = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        self.user_message = user_message or "抱歉，处理请求时出现了错误。"
        super().__init__(self.message)
