"""
统一错误处理模块
提供自定义异常类和错误处理工具
"""

import logging
from typing import Optional, Dict, Any
from .base_errors import TaimeiBotError as BaseTaimeiBotError, ErrorType

class APIError(BaseTaimeiBotError):
    """API相关错误"""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None,
                 original_error: Optional[Exception] = None):
        self.status_code = status_code
        self.response_data = response_data
        user_message = self._get_user_friendly_message(status_code)
        super().__init__(message, ErrorType.API_ERROR, original_error, user_message)

    def _get_user_friendly_message(self, status_code: Optional[int]) -> str:
        """根据状态码返回用户友好的错误消息"""
        if status_code == 401:
            return "API认证失败，请联系管理员检查配置。"
        elif status_code == 429:
            return "请求过于频繁，请稍后再试。"
        elif status_code >= 500:
            return "服务暂时不可用，请稍后再试。"
        elif status_code and status_code >= 400:
            return "请求参数有误，请检查后重试。"
        return "API调用失败，请稍后再试。"

class NetworkError(BaseTaimeiBotError):
    """网络相关错误"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        user_message = "网络连接失败，请检查网络后重试。"
        super().__init__(message, ErrorType.NETWORK_ERROR, original_error, user_message)

class ConfigError(BaseTaimeiBotError):
    """配置相关错误"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        user_message = "配置错误，请联系管理员检查配置。"
        super().__init__(message, ErrorType.CONFIG_ERROR, original_error, user_message)

class ValidationError(BaseTaimeiBotError):
    """验证相关错误"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        user_message = f"输入验证失败：{message}"
        super().__init__(message, ErrorType.VALIDATION_ERROR, original_error, user_message)

class FileError(BaseTaimeiBotError):
    """文件相关错误"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        user_message = "文件操作失败，请联系管理员检查。"
        super().__init__(message, ErrorType.FILE_ERROR, original_error, user_message)

class RateLimitError(BaseTaimeiBotError):
    """限流相关错误"""

    def __init__(self, message: str, retry_after: Optional[float] = None, original_error: Optional[Exception] = None):
        self.retry_after = retry_after
        user_message = f"请求过于频繁，请 {retry_after:.1f} 秒后重试" if retry_after else "请求过于频繁，请稍后重试。"
        # We can add a new ErrorType for rate limiting if desired, or reuse an existing one.
        # For now, let's reuse VALIDATION_ERROR as it's a form of request validation.
        super().__init__(message, ErrorType.VALIDATION_ERROR, original_error, user_message)

class CacheError(BaseTaimeiBotError):
    """缓存相关错误"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        user_message = "缓存服务暂时不可用，请稍后重试。"
        super().__init__(message, ErrorType.UNKNOWN_ERROR, original_error, user_message)

class ContainerError(BaseTaimeiBotError):
    """依赖注入容器相关错误"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        user_message = "服务容器内部错误，请联系管理员。"
        super().__init__(message, ErrorType.CONFIG_ERROR, original_error, user_message)

def handle_api_errors(func):
    """API错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"API调用失败: {str(e)}", exc_info=True)

            # 根据异常类型返回相应的错误
            if hasattr(e, 'response'):
                status_code = e.response.status_code
                try:
                    response_data = e.response.json()
                except:
                    response_data = None
                raise APIError(
                    f"API请求失败: {str(e)}",
                    status_code=status_code,
                    response_data=response_data,
                    original_error=e
                )
            elif isinstance(e, (ConnectionError, TimeoutError)):
                raise NetworkError(f"网络连接失败: {str(e)}", original_error=e)
            else:
                raise BaseTaimeiBotError(f"未知错误: {str(e)}", original_error=e)

    return wrapper

def handle_file_errors(func):
    """文件操作错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise FileError(f"文件未找到: {str(e)}", original_error=e)
        except PermissionError as e:
            raise FileError(f"文件权限错误: {str(e)}", original_error=e)
        except json.JSONDecodeError as e:
            raise FileError(f"JSON解析错误: {str(e)}", original_error=e)
        except Exception as e:
            raise FileError(f"文件操作失败: {str(e)}", original_error=e)

    return wrapper

def get_error_context(error: Exception) -> Dict[str, Any]:
    """获取错误上下文信息"""
    context = {
        'error_type': type(error).__name__,
        'error_message': str(error),
    }

    if isinstance(error, BaseTaimeiBotError):
        context.update({
            'taimei_error_type': error.error_type.value,
            'user_message': error.user_message,
        })

        if isinstance(error, APIError):
            context.update({
                'status_code': error.status_code,
                'response_data': error.response_data,
            })

    return context

def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None):
    """记录错误日志"""
    error_context = get_error_context(error)
    if context:
        error_context.update(context)

    logger.error(
        f"发生错误: {error_context['error_type']} - {error_context['error_message']}",
        extra={'error_context': error_context},
        exc_info=True
    )
