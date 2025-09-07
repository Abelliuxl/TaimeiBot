from khl import Bot, Message
from utils.logging_utils import get_logger
from utils.error_handler import APIError, NetworkError, log_error
import json
import os
from typing import Optional, Dict, Any, Union
from config.constants import DEFAULT_ERROR_MESSAGE

logger = get_logger(__name__)

class MessageService:
    """消息服务类"""
    
    def __init__(self, config_manager):
        """
        初始化消息服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        logger.info("消息服务初始化完成")

    async def update_message(self, msg_id: str, content: Union[str, Dict], target_id: Optional[str] = None, 
                           channel_type: str = 'public', bot: Optional[Bot] = None) -> Dict[str, Any]:
        """更新消息
        
        Args:
            msg_id: 消息ID
            content: 消息内容（字符串或字典）
            target_id: 目标ID（用于临时消息）
            channel_type: 频道类型（public/private）
            bot: 机器人实例
            
        Returns:
            更新结果
        """
        logger.info(f"更新消息 - msg_id: {msg_id}, content: {content}, target_id: {target_id}")
        
        try:
            if not isinstance(content, str):    
                content = json.dumps(content)
                
            data = {'msg_id': msg_id, 'content': content}
            if target_id is not None:
                data['temp_target_id'] = target_id
                
            if channel_type == 'public':
                result = await bot.client.gate.request('POST', 'message/update', data=data)
            else:
                result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
                
            logger.info(f"消息更新结果: {result}")
            return result
            
        except Exception as e:
            log_error(logger, e, {'msg_id': msg_id, 'channel_type': channel_type})
            raise APIError(f"更新消息失败: {str(e)}")

    async def send_to_channel(self, channel_id: str, content: str, bot: Bot) -> Dict[str, Any]:
        """发送消息到指定频道
        
        Args:
            channel_id: 频道ID
            content: 消息内容
            bot: 机器人实例
            
        Returns:
            发送结果
        """
        try:
            logger.info(f"发送消息到频道 {channel_id}: {content}")
            result = await bot.client.gate.request('POST', 'message/create', data={
                'channel_id': channel_id,
                'content': content
            })
            logger.info(f"发送消息结果: {result}")
            return result
        except Exception as e:
            log_error(logger, e, {'channel_id': channel_id})
            raise APIError(f"发送消息到频道失败: {str(e)}")

    async def send_direct_message(self, user_id: str, content: str, bot: Bot) -> Dict[str, Any]:
        """发送私信给指定用户
        
        Args:
            user_id: 用户ID
            content: 消息内容
            bot: 机器人实例
            
        Returns:
            发送结果
        """
        try:
            logger.info(f"发送私信给用户 {user_id}: {content}")
            result = await bot.client.gate.request('POST', 'direct-message/create', data={
                'target_id': user_id,
                'content': content
            })
            logger.info(f"发送私信结果: {result}")
            return result
        except Exception as e:
            log_error(logger, e, {'user_id': user_id})
            raise APIError(f"发送私信失败: {str(e)}")
    
    async def send_error_message(self, channel_id: str, error: Exception, bot: Bot, 
                               custom_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """发送错误消息
        
        Args:
            channel_id: 频道ID
            error: 异常对象
            bot: 机器人实例
            custom_message: 自定义错误消息
            
        Returns:
            发送结果
        """
        try:
            # 获取错误消息
            if custom_message:
                error_msg = custom_message
            else:
                feature_config = self.config_manager.get_feature_config()
                if feature_config.get('enable_random_reply', True):
                    error_msg = DEFAULT_ERROR_MESSAGE
                else:
                    error_msg = f"发生错误: {str(error)}"
            
            logger.warning(f"发送错误消息到频道 {channel_id}: {error_msg}")
            return await self.send_to_channel(channel_id, error_msg, bot)
            
        except Exception as e:
            log_error(logger, e, {'channel_id': channel_id, 'original_error': str(error)})
            return None
    
    async def send_typing_indicator(self, channel_id: str, bot: Bot) -> bool:
        """发送正在输入指示器
        
        Args:
            channel_id: 频道ID
            bot: 机器人实例
            
        Returns:
            是否成功
        """
        try:
            await bot.client.gate.request('POST', 'channel/typing', data={
                'channel_id': channel_id
            })
            logger.debug(f"发送正在输入指示器到频道 {channel_id}")
            return True
        except Exception as e:
            log_error(logger, e, {'channel_id': channel_id})
            return False

# 为了保持向后兼容，保留原有的函数接口
_message_service_instance: Optional[MessageService] = None

def get_message_service() -> MessageService:
    """获取消息服务实例（向后兼容函数）"""
    global _message_service_instance
    if _message_service_instance is None:
        try:
            from services.container import get_container
            container = get_container()
            _message_service_instance = container.get('message_service')
        except Exception:
            # 如果依赖注入容器不可用，使用传统方式
            if _message_service_instance is None:
                from config.config import get_config_manager
                config_manager = get_config_manager()
                _message_service_instance = MessageService(config_manager)
    return _message_service_instance

async def upd_msg(msg_id: str, content, target_id=None, channel_type='public', bot=None):
    """更新消息（向后兼容函数）"""
    service = get_message_service()
    return await service.update_message(msg_id, content, target_id, channel_type, bot)

async def send_to_channel(channel_id: str, content: str, bot: Bot):
    """发送消息到指定频道（向后兼容函数）"""
    service = get_message_service()
    return await service.send_to_channel(channel_id, content, bot)

async def send_direct_message(user_id: str, content: str, bot: Bot):
    """发送私信给指定用户（向后兼容函数）"""
    service = get_message_service()
    return await service.send_direct_message(user_id, content, bot)
