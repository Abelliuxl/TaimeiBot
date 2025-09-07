"""
限流器
提供统一的限流功能，支持多种限流策略和算法
"""

import asyncio
import time
from typing import Dict, Optional, Union, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from utils.logging_utils import get_logger
from utils.error_handler import RateLimitError, log_error
from config.constants import DEFAULT_RATE_LIMIT_REQUESTS, DEFAULT_RATE_LIMIT_WINDOW

logger = get_logger(__name__)

@dataclass
class RateLimitInfo:
    """限流信息"""
    is_limited: bool
    remaining_requests: int
    reset_time: float
    retry_after: Optional[float] = None

class RateLimiter:
    """限流器基类"""
    
    def __init__(self, max_requests: int, window_seconds: float):
        """
        初始化限流器
        
        Args:
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        logger.info(f"限流器初始化完成: {max_requests} 请求 / {window_seconds} 秒")
    
    async def check_rate_limit(self, key: str) -> RateLimitInfo:
        """
        检查限流状态
        
        Args:
            key: 限流键
            
        Returns:
            限流信息
        """
        raise NotImplementedError
    
    async def wait_if_needed(self, key: str) -> bool:
        """
        如果需要限流则等待
        
        Args:
            key: 限流键
            
        Returns:
            是否等待了
        """
        rate_info = await self.check_rate_limit(key)
        if rate_info.is_limited and rate_info.retry_after:
            await asyncio.sleep(rate_info.retry_after)
            return True
        return False

class TokenBucketRateLimiter(RateLimiter):
    """令牌桶限流器"""
    
    def __init__(self, max_requests: int, window_seconds: float):
        """
        初始化令牌桶限流器
        
        Args:
            max_requests: 最大请求数（桶容量）
            window_seconds: 时间窗口（秒）
        """
        super().__init__(max_requests, window_seconds)
        self._buckets: Dict[str, dict] = defaultdict(lambda: {
            'tokens': max_requests,
            'last_refill': time.time()
        })
    
    async def check_rate_limit(self, key: str) -> RateLimitInfo:
        """检查限流状态"""
        current_time = time.time()
        bucket = self._buckets[key]
        
        # 计算时间差
        time_diff = current_time - bucket['last_refill']
        
        # 补充令牌
        refill_tokens = int(time_diff * self.max_requests / self.window_seconds)
        if refill_tokens > 0:
            bucket['tokens'] = min(self.max_requests, bucket['tokens'] + refill_tokens)
            bucket['last_refill'] = current_time
        
        # 检查是否有足够的令牌
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return RateLimitInfo(
                is_limited=False,
                remaining_requests=int(bucket['tokens']),
                reset_time=bucket['last_refill'] + self.window_seconds
            )
        else:
            # 计算需要等待的时间
            retry_after = (1 - bucket['tokens']) * self.window_seconds / self.max_requests
            return RateLimitInfo(
                is_limited=True,
                remaining_requests=0,
                reset_time=current_time + retry_after,
                retry_after=retry_after
            )

class SlidingWindowRateLimiter(RateLimiter):
    """滑动窗口限流器"""
    
    def __init__(self, max_requests: int, window_seconds: float):
        """
        初始化滑动窗口限流器
        
        Args:
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        super().__init__(max_requests, window_seconds)
        self._windows: Dict[str, deque] = defaultdict(lambda: deque())
    
    async def check_rate_limit(self, key: str) -> RateLimitInfo:
        """检查限流状态"""
        current_time = time.time()
        window = self._windows[key]
        
        # 清理过期的请求记录
        while window and window[0] <= current_time - self.window_seconds:
            window.popleft()
        
        # 检查是否超过限制
        if len(window) < self.max_requests:
            window.append(current_time)
            return RateLimitInfo(
                is_limited=False,
                remaining_requests=self.max_requests - len(window),
                reset_time=window[0] + self.window_seconds if window else current_time
            )
        else:
            # 计算最早请求的过期时间
            retry_after = window[0] + self.window_seconds - current_time
            return RateLimitInfo(
                is_limited=True,
                remaining_requests=0,
                reset_time=window[0] + self.window_seconds,
                retry_after=retry_after
            )

class FixedWindowRateLimiter(RateLimiter):
    """固定窗口限流器"""
    
    def __init__(self, max_requests: int, window_seconds: float):
        """
        初始化固定窗口限流器
        
        Args:
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        super().__init__(max_requests, window_seconds)
        self._counters: Dict[str, dict] = defaultdict(lambda: {
            'count': 0,
            'window_start': time.time()
        })
    
    async def check_rate_limit(self, key: str) -> RateLimitInfo:
        """检查限流状态"""
        current_time = time.time()
        counter = self._counters[key]
        
        # 检查是否需要重置窗口
        if current_time - counter['window_start'] >= self.window_seconds:
            counter['count'] = 0
            counter['window_start'] = current_time
        
        # 检查是否超过限制
        if counter['count'] < self.max_requests:
            counter['count'] += 1
            return RateLimitInfo(
                is_limited=False,
                remaining_requests=self.max_requests - counter['count'],
                reset_time=counter['window_start'] + self.window_seconds
            )
        else:
            # 计算窗口重置时间
            retry_after = counter['window_start'] + self.window_seconds - current_time
            return RateLimitInfo(
                is_limited=True,
                remaining_requests=0,
                reset_time=counter['window_start'] + self.window_seconds,
                retry_after=retry_after
            )

class LeakyBucketRateLimiter(RateLimiter):
    """漏桶限流器"""
    
    def __init__(self, max_requests: int, window_seconds: float):
        """
        初始化漏桶限流器
        
        Args:
            max_requests: 桶容量
            window_seconds: 漏水速率（秒）
        """
        super().__init__(max_requests, window_seconds)
        self._buckets: Dict[str, dict] = defaultdict(lambda: {
            'water_level': 0,
            'last_leak': time.time()
        })
        self.leak_rate = 1.0 / window_seconds  # 每秒漏水的量
    
    async def check_rate_limit(self, key: str) -> RateLimitInfo:
        """检查限流状态"""
        current_time = time.time()
        bucket = self._buckets[key]
        
        # 计算漏水
        time_diff = current_time - bucket['last_leak']
        leak_amount = time_diff * self.leak_rate
        bucket['water_level'] = max(0, bucket['water_level'] - leak_amount)
        bucket['last_leak'] = current_time
        
        # 检查是否可以加水
        if bucket['water_level'] < self.max_requests:
            bucket['water_level'] += 1
            return RateLimitInfo(
                is_limited=False,
                remaining_requests=int(self.max_requests - bucket['water_level']),
                reset_time=current_time + (bucket['water_level'] / self.leak_rate)
            )
        else:
            # 计算需要等待的时间
            retry_after = (bucket['water_level'] - self.max_requests + 1) / self.leak_rate
            return RateLimitInfo(
                is_limited=True,
                remaining_requests=0,
                reset_time=current_time + retry_after,
                retry_after=retry_after
            )

# 限流器类型
class RateLimiterType(Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"

class RateLimitManager:
    """限流管理器"""
    
    def __init__(self):
        """初始化限流管理器"""
        self._limiters: Dict[str, RateLimiter] = {}
        logger.info("限流管理器初始化完成")
    
    def create_limiter(self, name: str, limiter_type: RateLimiterType, 
                     max_requests: int, window_seconds: float) -> RateLimiter:
        """
        创建限流器
        
        Args:
            name: 限流器名称
            limiter_type: 限流器类型
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            限流器实例
        """
        if limiter_type == RateLimiterType.TOKEN_BUCKET:
            limiter = TokenBucketRateLimiter(max_requests, window_seconds)
        elif limiter_type == RateLimiterType.SLIDING_WINDOW:
            limiter = SlidingWindowRateLimiter(max_requests, window_seconds)
        elif limiter_type == RateLimiterType.FIXED_WINDOW:
            limiter = FixedWindowRateLimiter(max_requests, window_seconds)
        elif limiter_type == RateLimiterType.LEAKY_BUCKET:
            limiter = LeakyBucketRateLimiter(max_requests, window_seconds)
        else:
            raise ValueError(f"不支持的限流器类型: {limiter_type}")
        
        self._limiters[name] = limiter
        logger.info(f"创建限流器: {name} ({limiter_type.value})")
        return limiter
    
    def get_limiter(self, name: str) -> Optional[RateLimiter]:
        """
        获取限流器
        
        Args:
            name: 限流器名称
            
        Returns:
            限流器实例
        """
        return self._limiters.get(name)
    
    async def check_limit(self, limiter_name: str, key: str) -> RateLimitInfo:
        """
        检查限流
        
        Args:
            limiter_name: 限流器名称
            key: 限流键
            
        Returns:
            限流信息
        """
        limiter = self.get_limiter(limiter_name)
        if not limiter:
            raise ValueError(f"限流器不存在: {limiter_name}")
        
        return await limiter.check_rate_limit(key)
    
    async def wait_if_needed(self, limiter_name: str, key: str) -> bool:
        """
        如果需要限流则等待
        
        Args:
            limiter_name: 限流器名称
            key: 限流键
            
        Returns:
            是否等待了
        """
        limiter = self.get_limiter(limiter_name)
        if not limiter:
            raise ValueError(f"限流器不存在: {limiter_name}")
        
        return await limiter.wait_if_needed(key)

# 限流装饰器
def rate_limit(limiter_name: str, key_func: Optional[Callable] = None, 
               raise_exception: bool = False):
    """
    限流装饰器
    
    Args:
        limiter_name: 限流器名称
        key_func: 限流键生成函数
        raise_exception: 是否抛出异常
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # 获取限流管理器
                manager = get_rate_limit_manager()
                
                # 生成限流键
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    # 默认使用函数名和第一个参数
                    key = f"{func.__name__}:{args[0] if args else 'default'}"
                
                # 检查限流
                rate_info = await manager.check_limit(limiter_name, key)
                
                if rate_info.is_limited:
                    if raise_exception:
                        raise RateLimitError(f"请求过于频繁，请 {rate_info.retry_after:.1f} 秒后重试")
                    else:
                        logger.warning(f"限流触发: {key}, 重试时间: {rate_info.retry_after:.1f}秒")
                        return None
                
                # 执行原函数
                return await func(*args, **kwargs)
                
            except Exception as e:
                log_error(logger, e, {'function': 'rate_limit_wrapper', 'limiter_name': limiter_name})
                if raise_exception:
                    raise
                return None
        
        return wrapper
    return decorator

# 全局限流管理器实例
_rate_limit_manager: Optional[RateLimitManager] = None

def get_rate_limit_manager() -> RateLimitManager:
    """获取限流管理器"""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
        
        # 创建默认的限流器
        _rate_limit_manager.create_limiter(
            "api", 
            RateLimiterType.TOKEN_BUCKET, 
            DEFAULT_RATE_LIMIT_REQUESTS, 
            DEFAULT_RATE_LIMIT_WINDOW
        )
        
        _rate_limit_manager.create_limiter(
            "command", 
            RateLimiterType.SLIDING_WINDOW, 
            30,  # 每分钟30个命令
            60
        )
        
        _rate_limit_manager.create_limiter(
            "talent", 
            RateLimiterType.FIXED_WINDOW, 
            10,  # 每分钟10个天赋查询
            60
        )
        
        _rate_limit_manager.create_limiter(
            "translation", 
            RateLimiterType.LEAKY_BUCKET, 
            20,  # 每分钟20个翻译请求
            60
        )
        
        _rate_limit_manager.create_limiter(
            "ai_chat", 
            RateLimiterType.TOKEN_BUCKET, 
            15,  # 每分钟15个AI聊天请求
            60
        )
        
        logger.info("默认限流器创建完成")
    
    return _rate_limit_manager

# 便捷的限流函数
async def check_api_rate_limit(user_id: str) -> RateLimitInfo:
    """检查API限流"""
    manager = get_rate_limit_manager()
    return await manager.check_limit("api", f"api:{user_id}")

async def check_command_rate_limit(user_id: str) -> RateLimitInfo:
    """检查命令限流"""
    manager = get_rate_limit_manager()
    return await manager.check_limit("command", f"command:{user_id}")

async def check_talent_rate_limit(user_id: str) -> RateLimitInfo:
    """检查天赋查询限流"""
    manager = get_rate_limit_manager()
    return await manager.check_limit("talent", f"talent:{user_id}")

async def check_translation_rate_limit(user_id: str) -> RateLimitInfo:
    """检查翻译限流"""
    manager = get_rate_limit_manager()
    return await manager.check_limit("translation", f"translation:{user_id}")

async def check_ai_chat_rate_limit(user_id: str) -> RateLimitInfo:
    """检查AI聊天限流"""
    manager = get_rate_limit_manager()
    return await manager.check_limit("ai_chat", f"ai_chat:{user_id}")

# 限流装饰器的便捷函数
def api_rate_limit(key_func: Optional[Callable] = None, raise_exception: bool = False):
    """API限流装饰器"""
    return rate_limit("api", key_func, raise_exception)

def command_rate_limit(key_func: Optional[Callable] = None, raise_exception: bool = False):
    """命令限流装饰器"""
    return rate_limit("command", key_func, raise_exception)

def talent_rate_limit(key_func: Optional[Callable] = None, raise_exception: bool = False):
    """天赋查询限流装饰器"""
    return rate_limit("talent", key_func, raise_exception)

def translation_rate_limit(key_func: Optional[Callable] = None, raise_exception: bool = False):
    """翻译限流装饰器"""
    return rate_limit("translation", key_func, raise_exception)

def ai_chat_rate_limit(key_func: Optional[Callable] = None, raise_exception: bool = False):
    """AI聊天限流装饰器"""
    return rate_limit("ai_chat", key_func, raise_exception)
