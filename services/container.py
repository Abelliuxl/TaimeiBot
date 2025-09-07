"""
依赖注入容器
实现服务依赖注入，降低模块间耦合度
"""

import asyncio
from typing import Dict, Any, Optional, TypeVar, Type, Callable
from utils.logging_utils import get_logger
from utils.error_handler import ContainerError, log_error

logger = get_logger(__name__)

T = TypeVar('T')

class ServiceContainer:
    """服务容器，实现依赖注入"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._initialized = False
        
    def register(self, service_name: str, factory: Callable, singleton: bool = False) -> None:
        """注册服务
        
        Args:
            service_name: 服务名称
            factory: 服务工厂函数
            singleton: 是否为单例服务
        """
        try:
            if singleton:
                self._factories[service_name] = factory
            else:
                self._factories[service_name] = factory
                
            logger.debug(f"服务 {service_name} 注册成功")
        except Exception as e:
            log_error(logger, e, {'function': 'register', 'service_name': service_name})
            raise ContainerError(f"注册服务 {service_name} 失败: {str(e)}")
    
    def register_instance(self, service_name: str, instance: Any) -> None:
        """注册服务实例
        
        Args:
            service_name: 服务名称
            instance: 服务实例
        """
        try:
            self._services[service_name] = instance
            logger.debug(f"服务实例 {service_name} 注册成功")
        except Exception as e:
            log_error(logger, e, {'function': 'register_instance', 'service_name': service_name})
            raise ContainerError(f"注册服务实例 {service_name} 失败: {str(e)}")
    
    def get(self, service_name: str) -> Any:
        """获取服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务实例
        """
        try:
            # 首先检查已注册的实例
            if service_name in self._services:
                return self._services[service_name]
            
            # 检查单例
            if service_name in self._singletons:
                return self._singletons[service_name]
            
            # 检查工厂函数
            if service_name in self._factories:
                factory = self._factories[service_name]
                instance = factory(self)
                
                # 如果是单例，缓存实例
                if service_name in self._factories and asyncio.iscoroutinefunction(factory):
                    self._singletons[service_name] = instance
                elif service_name in self._factories:
                    self._singletons[service_name] = instance
                
                return instance
            
            raise ContainerError(f"服务 {service_name} 未注册")
            
        except Exception as e:
            log_error(logger, e, {'function': 'get', 'service_name': service_name})
            raise ContainerError(f"获取服务 {service_name} 失败: {str(e)}")
    
    async def get_async(self, service_name: str) -> Any:
        """异步获取服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务实例
        """
        try:
            # 首先检查已注册的实例
            if service_name in self._services:
                return self._services[service_name]
            
            # 检查单例
            if service_name in self._singletons:
                return self._singletons[service_name]
            
            # 检查工厂函数
            if service_name in self._factories:
                factory = self._factories[service_name]
                
                if asyncio.iscoroutinefunction(factory):
                    instance = await factory(self)
                else:
                    instance = factory(self)
                
                # 缓存实例
                self._singletons[service_name] = instance
                return instance
            
            raise ContainerError(f"服务 {service_name} 未注册")
            
        except Exception as e:
            log_error(logger, e, {'function': 'get_async', 'service_name': service_name})
            raise ContainerError(f"获取服务 {service_name} 失败: {str(e)}")
    
    def has_service(self, service_name: str) -> bool:
        """检查服务是否存在
        
        Args:
            service_name: 服务名称
            
        Returns:
            是否存在
        """
        return (service_name in self._services or 
                service_name in self._singletons or 
                service_name in self._factories)
    
    def remove(self, service_name: str) -> bool:
        """移除服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            是否成功移除
        """
        try:
            removed = False
            
            if service_name in self._services:
                del self._services[service_name]
                removed = True
            
            if service_name in self._singletons:
                del self._singletons[service_name]
                removed = True
            
            if service_name in self._factories:
                del self._factories[service_name]
                removed = True
            
            if removed:
                logger.debug(f"服务 {service_name} 移除成功")
            
            return removed
            
        except Exception as e:
            log_error(logger, e, {'function': 'remove', 'service_name': service_name})
            raise ContainerError(f"移除服务 {service_name} 失败: {str(e)}")
    
    def clear(self) -> None:
        """清空所有服务"""
        try:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            logger.debug("所有服务已清空")
        except Exception as e:
            log_error(logger, e, {'function': 'clear'})
            raise ContainerError(f"清空服务失败: {str(e)}")
    
    def get_services(self) -> Dict[str, Any]:
        """获取所有服务实例
        
        Returns:
            服务实例字典
        """
        services = {}
        services.update(self._services)
        services.update(self._singletons)
        return services
    
    def is_initialized(self) -> bool:
        """检查容器是否已初始化"""
        return self._initialized
    
    def set_initialized(self, initialized: bool) -> None:
        """设置容器初始化状态"""
        self._initialized = initialized

# 全局容器实例
_container: Optional[ServiceContainer] = None

def get_container() -> ServiceContainer:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container

def initialize_container() -> ServiceContainer:
    """初始化容器"""
    global _container
    _container = ServiceContainer()
    _container.set_initialized(True)
    logger.info("依赖注入容器初始化完成")
    return _container

# 装饰器用于依赖注入
def inject(service_name: str):
    """依赖注入装饰器
    
    Args:
        service_name: 服务名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            container = get_container()
            service = container.get(service_name)
            return func(*args, service, **kwargs)
        return wrapper
    return decorator

def inject_async(service_name: str):
    """异步依赖注入装饰器
    
    Args:
        service_name: 服务名称
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            container = get_container()
            service = await container.get_async(service_name)
            return await func(*args, service, **kwargs)
        return wrapper
    return decorator

# 服务工厂函数
def create_config_manager(container: ServiceContainer):
    """创建配置管理器"""
    from config.config import get_config_manager
    return get_config_manager()

def create_raider_service(container: ServiceContainer):
    """创建Raider服务"""
    from services.raider_service import RaiderService
    config_manager = container.get('config_manager')
    return RaiderService(config_manager)

def create_llm_service(container: ServiceContainer):
    """创建LLM服务"""
    from services.llm_service import LLMService
    config_manager = container.get('config_manager')
    return LLMService(config_manager)

def create_message_service(container: ServiceContainer):
    """创建消息服务"""
    from services.message_service import MessageService
    config_manager = container.get('config_manager')
    return MessageService(config_manager)

async def create_data_repositories(container: ServiceContainer):
    """创建数据仓库"""
    from services.data.config_repository import ConfigRepository
    from services.data.game_data_repository import GameDataRepository
    from services.data.player_repository import PlayerRepository
    
    config_manager = container.get('config_manager')
    
    config_repo = ConfigRepository(config_manager)
    game_data_repo = GameDataRepository(config_manager)
    player_repo = PlayerRepository(config_manager)
    
    return {
        'config_repository': config_repo,
        'game_data_repository': game_data_repo,
        'player_repository': player_repo
    }

def register_services(container: ServiceContainer) -> None:
    """注册所有服务
    
    Args:
        container: 服务容器
    """
    try:
        # 注册配置管理器（单例）
        container.register('config_manager', create_config_manager, singleton=True)
        
        # 注册数据仓库（单例）
        container.register('data_repositories', create_data_repositories, singleton=True)
        
        # 注册业务服务（单例）
        container.register('raider_service', create_raider_service, singleton=True)
        container.register('llm_service', create_llm_service, singleton=True)
        container.register('message_service', create_message_service, singleton=True)
        
        logger.info("所有服务注册完成")
        
    except Exception as e:
        log_error(logger, e, {'function': 'register_services'})
        raise ContainerError(f"注册服务失败: {str(e)}")

async def initialize_services() -> ServiceContainer:
    """初始化所有服务
    
    Returns:
        初始化完成的服务容器
    """
    try:
        container = initialize_container()
        
        # 注册所有服务
        register_services(container)
        
        # 预初始化关键服务
        await container.get_async('config_manager')
        await container.get_async('data_repositories')
        
        logger.info("所有服务初始化完成")
        return container
        
    except Exception as e:
        log_error(logger, e, {'function': 'initialize_services'})
        raise ContainerError(f"初始化服务失败: {str(e)}")
