"""
重试装饰器模块
提供API调用的重试机制
"""

import asyncio
import functools
import logging
import time
from typing import Callable, Optional, Union, Any
from .base_errors import TaimeiBotError
from .error_handler import APIError, NetworkError

logger = logging.getLogger(__name__)

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (APIError, NetworkError, ConnectionError, TimeoutError),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试，直接抛出异常
                        logger.error(f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，"
                        f"将在 {current_delay:.1f} 秒后重试。错误: {str(e)}"
                    )
                    
                    # 调用重试回调
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.error(f"重试回调函数执行失败: {str(callback_error)}")
                    
                    # 等待延迟时间
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception or TaimeiBotError("重试失败")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试，直接抛出异常
                        logger.error(f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，"
                        f"将在 {current_delay:.1f} 秒后重试。错误: {str(e)}"
                    )
                    
                    # 调用重试回调
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.error(f"重试回调函数执行失败: {str(callback_error)}")
                    
                    # 等待延迟时间
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception or TaimeiBotError("重试失败")
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def retry_with_context(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (APIError, NetworkError, ConnectionError, TimeoutError),
    context_extractor: Optional[Callable] = None
):
    """
    带上下文的重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        context_extractor: 上下文提取函数，用于记录重试上下文
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试，直接抛出异常
                        error_context = {}
                        if context_extractor:
                            try:
                                error_context = context_extractor(*args, **kwargs)
                            except Exception:
                                pass
                        
                        logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败",
                            extra={'retry_context': error_context}
                        )
                        raise
                    
                    # 记录重试上下文
                    error_context = {}
                    if context_extractor:
                        try:
                            error_context = context_extractor(*args, **kwargs)
                        except Exception:
                            pass
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，"
                        f"将在 {current_delay:.1f} 秒后重试",
                        extra={'retry_context': error_context}
                    )
                    
                    # 等待延迟时间
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception or TaimeiBotError("重试失败")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试，直接抛出异常
                        error_context = {}
                        if context_extractor:
                            try:
                                error_context = context_extractor(*args, **kwargs)
                            except Exception:
                                pass
                        
                        logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败",
                            extra={'retry_context': error_context}
                        )
                        raise
                    
                    # 记录重试上下文
                    error_context = {}
                    if context_extractor:
                        try:
                            error_context = context_extractor(*args, **kwargs)
                        except Exception:
                            pass
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，"
                        f"将在 {current_delay:.1f} 秒后重试",
                        extra={'retry_context': error_context}
                    )
                    
                    # 等待延迟时间
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception or TaimeiBotError("重试失败")
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class RetryConfig:
    """重试配置类"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (APIError, NetworkError, ConnectionError, TimeoutError)
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions

def get_default_retry_config() -> RetryConfig:
    """获取默认重试配置"""
    return RetryConfig()

def get_aggressive_retry_config() -> RetryConfig:
    """获取激进重试配置（更多重试次数）"""
    return RetryConfig(max_attempts=5, delay=0.5, backoff=1.5)

def get_conservative_retry_config() -> RetryConfig:
    """获取保守重试配置（更少重试次数）"""
    return RetryConfig(max_attempts=2, delay=2.0, backoff=3.0)
