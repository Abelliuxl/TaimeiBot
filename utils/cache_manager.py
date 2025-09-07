"""
缓存管理器
提供统一的缓存操作接口，支持多种缓存策略
"""

import asyncio
import json
import time
import threading
from typing import Any, Dict, Optional, Union, Callable, Awaitable
from collections import defaultdict
from utils.logging_utils import get_logger
from utils.error_handler import CacheError, log_error
from config.constants import DEFAULT_CACHE_TTL, DEFAULT_RAIDER_CACHE_TTL, DEFAULT_TRANSLATION_CACHE_TTL

logger = get_logger(__name__)

class CacheEntry:
    """缓存条目类"""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        """
        初始化缓存条目
        
        Args:
            value: 缓存值
            ttl: 生存时间（秒），None表示永不过期
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def get_value(self) -> Any:
        """获取值并更新访问信息"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def get_age(self) -> float:
        """获取缓存年龄（秒）"""
        return time.time() - self.created_at
    
    def get_time_since_last_access(self) -> float:
        """获取距上次访问的时间（秒）"""
        return time.time() - self.last_accessed

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = DEFAULT_CACHE_TTL, max_size: int = 1000):
        """
        初始化缓存管理器
        
        Args:
            default_ttl: 默认生存时间（秒）
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = threading.RLock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # 缓存统计
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        logger.info(f"缓存管理器初始化完成，默认TTL: {default_ttl}秒，最大容量: {max_size}")
    
    async def start(self) -> None:
        """启动缓存管理器"""
        if self._is_running:
            return
        
        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("缓存管理器启动完成")
    
    async def stop(self) -> None:
        """停止缓存管理器"""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("缓存管理器停止完成")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return default
            
            if entry.is_expired():
                self._remove_entry(key)
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return default
            
            self._stats['hits'] += 1
            return entry.get_value()
    
    async def get_async(self, key: str, default: Any = None) -> Any:
        """异步获取缓存值"""
        return self.get(key, default)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认值
        """
        with self._lock:
            # 检查容量限制
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_lru()
            
            # 创建缓存条目
            entry_ttl = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(value, entry_ttl)
            
            logger.debug(f"缓存设置成功: {key}, TTL: {entry_ttl}秒")
    
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """异步设置缓存值"""
        self.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        with self._lock:
            return self._remove_entry(key)
    
    async def delete_async(self, key: str) -> bool:
        """异步删除缓存值"""
        return self.delete(key)
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            if entry.is_expired():
                self._remove_entry(key)
                return False
            
            return True
    
    async def exists_async(self, key: str) -> bool:
        """异步检查缓存是否存在"""
        return self.exists(key)
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("所有缓存已清空")
    
    async def clear_async(self) -> None:
        """异步清空所有缓存"""
        self.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations']
            }
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """异步获取缓存统计信息"""
        return self.get_stats()
    
    def _remove_entry(self, key: str) -> bool:
        """移除缓存条目"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def _evict_lru(self) -> None:
        """淘汰最近最少使用的缓存条目"""
        if not self._cache:
            return
        
        # 找到最近最少使用的条目
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].get_time_since_last_access())
        
        self._remove_entry(lru_key)
        self._stats['evictions'] += 1
        logger.debug(f"淘汰缓存条目: {lru_key}")
    
    async def _cleanup_loop(self) -> None:
        """清理过期缓存的循环任务"""
        while self._is_running:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error(logger, e, {'function': '_cleanup_loop'})
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
                self._stats['expirations'] += 1
            
            if expired_keys:
                logger.debug(f"清理过期缓存: {len(expired_keys)} 个条目")

# 专门的缓存管理器
class RaiderCacheManager(CacheManager):
    """Raider.io API缓存管理器"""
    
    def __init__(self):
        super().__init__(default_ttl=DEFAULT_RAIDER_CACHE_TTL, max_size=500)
        logger.info("Raider.io缓存管理器初始化完成")

class TranslationCacheManager(CacheManager):
    """翻译缓存管理器"""
    
    def __init__(self):
        super().__init__(default_ttl=DEFAULT_TRANSLATION_CACHE_TTL, max_size=1000)
        logger.info("翻译缓存管理器初始化完成")

# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None
_raider_cache_manager: Optional[RaiderCacheManager] = None
_translation_cache_manager: Optional[TranslationCacheManager] = None

def get_cache_manager() -> CacheManager:
    """获取通用缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def get_raider_cache_manager() -> RaiderCacheManager:
    """获取Raider.io缓存管理器"""
    global _raider_cache_manager
    if _raider_cache_manager is None:
        _raider_cache_manager = RaiderCacheManager()
    return _raider_cache_manager

def get_translation_cache_manager() -> TranslationCacheManager:
    """获取翻译缓存管理器"""
    global _translation_cache_manager
    if _translation_cache_manager is None:
        _translation_cache_manager = TranslationCacheManager()
    return _translation_cache_manager

async def initialize_cache_managers() -> None:
    """初始化所有缓存管理器"""
    try:
        managers = [
            get_cache_manager(),
            get_raider_cache_manager(),
            get_translation_cache_manager()
        ]
        
        for manager in managers:
            await manager.start()
        
        logger.info("所有缓存管理器初始化完成")
    except Exception as e:
        log_error(logger, e, {'function': 'initialize_cache_managers'})
        raise CacheError(f"初始化缓存管理器失败: {str(e)}")

async def cleanup_cache_managers() -> None:
    """清理所有缓存管理器"""
    try:
        managers = [
            get_cache_manager(),
            get_raider_cache_manager(),
            get_translation_cache_manager()
        ]
        
        for manager in managers:
            await manager.stop()
        
        logger.info("所有缓存管理器清理完成")
    except Exception as e:
        log_error(logger, e, {'function': 'cleanup_cache_managers'})
        raise CacheError(f"清理缓存管理器失败: {str(e)}")
