"""
缓存装饰器
提供简单易用的缓存装饰器，支持函数和异步函数的缓存
"""

import asyncio
import functools
import hashlib
import json
from typing import Any, Callable, Optional, Union, Dict, Tuple
from utils.logging_utils import get_logger
from utils.error_handler import CacheError, log_error
from utils.cache_manager import get_cache_manager, get_raider_cache_manager, get_translation_cache_manager

logger = get_logger(__name__)

def _generate_cache_key(func: Callable, args: Tuple, kwargs: Dict, 
                       key_prefix: Optional[str] = None) -> str:
    """
    生成缓存键
    
    Args:
        func: 被装饰的函数
        args: 位置参数
        kwargs: 关键字参数
        key_prefix: 键前缀
        
    Returns:
        缓存键
    """
    try:
        # 构建键的基础部分
        key_parts = []
        
        if key_prefix:
            key_parts.append(key_prefix)
        
        # 添加函数名
        key_parts.append(func.__name__)
        
        # 添加模块名
        if func.__module__:
            key_parts.append(func.__module__)
        
        # 序列化参数
        try:
            # 尝试JSON序列化
            args_str = json.dumps(args, sort_keys=True, default=str)
            kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
            key_parts.append(args_str)
            key_parts.append(kwargs_str)
        except (TypeError, ValueError):
            # 如果JSON序列化失败，使用字符串表示
            key_parts.append(str(args))
            key_parts.append(str(kwargs))
        
        # 组合键并计算哈希
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        return f"{func.__module__}.{func.__name__}:{key_hash}"
        
    except Exception as e:
        log_error(logger, e, {'function': '_generate_cache_key', 'func_name': func.__name__})
        # 如果生成键失败，使用简单的键
        return f"{func.__module__}.{func.__name__}:{hash(str(args) + str(kwargs))}"

def cache(ttl: Optional[int] = None, key_prefix: Optional[str] = None, 
         cache_manager: Optional[Any] = None, ignore_args: Optional[list] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_prefix: 缓存键前缀
        cache_manager: 缓存管理器实例
        ignore_args: 要忽略的参数名列表
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 获取缓存管理器
                manager = cache_manager or get_cache_manager()
                
                # 处理要忽略的参数
                filtered_kwargs = kwargs.copy()
                if ignore_args:
                    for arg_name in ignore_args:
                        filtered_kwargs.pop(arg_name, None)
                
                # 生成缓存键
                cache_key = _generate_cache_key(func, args, filtered_kwargs, key_prefix)
                
                # 尝试从缓存获取
                cached_result = manager.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result
                
                # 缓存未命中，执行函数
                logger.debug(f"缓存未命中，执行函数: {cache_key}")
                result = func(*args, **kwargs)
                
                # 将结果存入缓存
                manager.set(cache_key, result, ttl)
                logger.debug(f"缓存设置: {cache_key}")
                
                return result
                
            except Exception as e:
                log_error(logger, e, {'function': 'cache_wrapper', 'func_name': func.__name__})
                # 如果缓存操作失败，直接执行函数
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def async_cache(ttl: Optional[int] = None, key_prefix: Optional[str] = None, 
                cache_manager: Optional[Any] = None, ignore_args: Optional[list] = None,
                enable_user_cache: bool = False):
    """
    异步缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_prefix: 缓存键前缀
        cache_manager: 缓存管理器实例
        ignore_args: 要忽略的参数名列表
        enable_user_cache: 是否启用用户级缓存（为不同用户生成不同缓存）
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # 获取缓存管理器
                manager = cache_manager or get_cache_manager()
                
                # 处理要忽略的参数
                filtered_kwargs = kwargs.copy()
                if ignore_args:
                    for arg_name in ignore_args:
                        filtered_kwargs.pop(arg_name, None)
                
                # 如果启用用户级缓存，确保user_id参与缓存键生成
                if enable_user_cache:
                    # 从kwargs中获取user_id，如果没有则使用默认值
                    user_id = filtered_kwargs.get('user_id', 'default_user')
                    # 为不同用户添加随机因子，避免完全相同的回复
                    import time
                    import hashlib
                    time_factor = int(time.time() / 300)  # 每5分钟变化一次
                    user_factor = hashlib.md5(f"{user_id}_{time_factor}".encode()).hexdigest()[:8]
                    filtered_kwargs['cache_variation'] = user_factor
                
                # 生成缓存键
                cache_key = _generate_cache_key(func, args, filtered_kwargs, key_prefix)
                
                # 尝试从缓存获取
                cached_result = await manager.get_async(cache_key)
                if cached_result is not None:
                    logger.debug(f"异步缓存命中: {cache_key}")
                    return cached_result
                
                # 缓存未命中，执行函数
                logger.debug(f"异步缓存未命中，执行函数: {cache_key}")
                result = await func(*args, **kwargs)
                
                # 将结果存入缓存
                await manager.set_async(cache_key, result, ttl)
                logger.debug(f"异步缓存设置: {cache_key}")
                
                return result
                
            except Exception as e:
                log_error(logger, e, {'function': 'async_cache_wrapper', 'func_name': func.__name__})
                # 如果缓存操作失败，直接执行函数
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def raider_cache(ttl: Optional[int] = None, key_prefix: Optional[str] = None, 
                 ignore_args: Optional[list] = None):
    """
    Raider.io API专用缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_prefix: 缓存键前缀
        ignore_args: 要忽略的参数名列表
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # 获取Raider.io专用缓存管理器
                manager = get_raider_cache_manager()
                
                # 处理要忽略的参数
                filtered_kwargs = kwargs.copy()
                if ignore_args:
                    for arg_name in ignore_args:
                        filtered_kwargs.pop(arg_name, None)
                
                # 生成缓存键
                cache_key = _generate_cache_key(func, args, filtered_kwargs, key_prefix or "raider")
                
                # 尝试从缓存获取
                cached_result = await manager.get_async(cache_key)
                if cached_result is not None:
                    logger.debug(f"Raider缓存命中: {cache_key}")
                    return cached_result
                
                # 缓存未命中，执行函数
                logger.debug(f"Raider缓存未命中，执行函数: {cache_key}")
                result = await func(*args, **kwargs)
                
                # 将结果存入缓存
                await manager.set_async(cache_key, result, ttl)
                logger.debug(f"Raider缓存设置: {cache_key}")
                
                return result
                
            except Exception as e:
                log_error(logger, e, {'function': 'raider_cache_wrapper', 'func_name': func.__name__})
                # 如果缓存操作失败，直接执行函数
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def translation_cache(ttl: Optional[int] = None, key_prefix: Optional[str] = None, 
                     ignore_args: Optional[list] = None):
    """
    翻译专用缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_prefix: 缓存键前缀
        ignore_args: 要忽略的参数名列表
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # 获取翻译专用缓存管理器
                manager = get_translation_cache_manager()
                
                # 处理要忽略的参数
                filtered_kwargs = kwargs.copy()
                if ignore_args:
                    for arg_name in ignore_args:
                        filtered_kwargs.pop(arg_name, None)
                
                # 生成缓存键
                cache_key = _generate_cache_key(func, args, filtered_kwargs, key_prefix or "translation")
                
                # 尝试从缓存获取
                cached_result = await manager.get_async(cache_key)
                if cached_result is not None:
                    logger.debug(f"翻译缓存命中: {cache_key}")
                    return cached_result
                
                # 缓存未命中，执行函数
                logger.debug(f"翻译缓存未命中，执行函数: {cache_key}")
                result = await func(*args, **kwargs)
                
                # 将结果存入缓存
                await manager.set_async(cache_key, result, ttl)
                logger.debug(f"翻译缓存设置: {cache_key}")
                
                return result
                
            except Exception as e:
                log_error(logger, e, {'function': 'translation_cache_wrapper', 'func_name': func.__name__})
                # 如果缓存操作失败，直接执行函数
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def cache_result(ttl: Optional[int] = None, key: Optional[str] = None, 
                cache_manager: Optional[Any] = None):
    """
    缓存结果的装饰器（用于手动指定键）
    
    Args:
        ttl: 缓存生存时间（秒）
        key: 手动指定的缓存键
        cache_manager: 缓存管理器实例
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 获取缓存管理器
                manager = cache_manager or get_cache_manager()
                
                # 使用手动指定的键或生成键
                cache_key = key or _generate_cache_key(func, args, kwargs)
                
                # 尝试从缓存获取
                cached_result = manager.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"结果缓存命中: {cache_key}")
                    return cached_result
                
                # 缓存未命中，执行函数
                logger.debug(f"结果缓存未命中，执行函数: {cache_key}")
                result = func(*args, **kwargs)
                
                # 将结果存入缓存
                manager.set(cache_key, result, ttl)
                logger.debug(f"结果缓存设置: {cache_key}")
                
                return result
                
            except Exception as e:
                log_error(logger, e, {'function': 'cache_result_wrapper', 'func_name': func.__name__})
                # 如果缓存操作失败，直接执行函数
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def clear_cache(pattern: Optional[str] = None, cache_manager: Optional[Any] = None):
    """
    清除缓存的装饰器
    
    Args:
        pattern: 要清除的缓存键模式
        cache_manager: 缓存管理器实例
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 清除缓存
                manager = cache_manager or get_cache_manager()
                
                if pattern:
                    # 如果指定了模式，清除匹配的缓存
                    # 这里简化处理，实际应用中可能需要更复杂的模式匹配
                    logger.debug(f"清除匹配模式 '{pattern}' 的缓存")
                    # 注意：这里需要根据实际需求实现模式匹配逻辑
                else:
                    # 清除所有缓存
                    manager.clear()
                    logger.debug("清除所有缓存")
                
                return result
                
            except Exception as e:
                log_error(logger, e, {'function': 'clear_cache_wrapper', 'func_name': func.__name__})
                # 如果清除缓存失败，仍然返回函数结果
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# 使用示例和便捷函数
def cached_function(ttl: int = 3600):
    """便捷的函数缓存装饰器"""
    return cache(ttl=ttl)

def cached_async_function(ttl: int = 3600):
    """便捷的异步函数缓存装饰器"""
    return async_cache(ttl=ttl)
