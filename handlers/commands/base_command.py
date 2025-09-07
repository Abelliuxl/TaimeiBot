"""
基础命令类
定义所有命令的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from khl import Message, Bot
from utils.logging_utils import get_logger
from utils.base_errors import TaimeiBotError
from utils.error_handler import ValidationError, log_error

logger = get_logger(__name__)

class BaseCommand(ABC):
    """命令基类"""
    
    def __init__(self, name: str, description: str, aliases: List[str] = None):
        self.name = name
        self.description = description
        self.aliases = aliases or []
        self.bot: Optional[Bot] = None
        self.config: Optional[Dict[str, Any]] = None
    
    def set_context(self, bot: Bot, config: Dict[str, Any]):
        """设置命令执行上下文"""
        self.bot = bot
        self.config = config
    
    @abstractmethod
    async def execute(self, message: Message, args: List[str]) -> Optional[str]:
        """
        执行命令
        
        Args:
            message: 消息对象
            args: 命令参数列表
            
        Returns:
            执行结果消息，如果不需要回复则返回None
        """
        pass
    
    @abstractmethod
    def validate_args(self, args: List[str]) -> bool:
        """
        验证命令参数
        
        Args:
            args: 命令参数列表
            
        Returns:
            参数是否有效
        """
        pass
    
    def can_handle(self, command_text: str) -> bool:
        """
        检查是否能处理给定的命令文本
        
        Args:
            command_text: 命令文本
            
        Returns:
            是否能处理该命令
        """
        command_text = command_text.lower().strip()
        return (command_text == self.name.lower() or 
                command_text in [alias.lower() for alias in self.aliases])
    
    def get_help_text(self) -> str:
        """获取帮助文本"""
        aliases_text = f" (别名: {', '.join(self.aliases)})" if self.aliases else ""
        return f"**{self.name}**{aliases_text} - {self.description}"
    
    async def send_error_reply(self, message: Message, error_message: str):
        """发送错误回复"""
        try:
            await message.reply(f"❌ {error_message}")
        except Exception as e:
            logger.error(f"发送错误回复失败: {str(e)}")
    
    async def send_success_reply(self, message: Message, content: str):
        """发送成功回复"""
        try:
            await message.reply(f"✅ {content}")
        except Exception as e:
            logger.error(f"发送成功回复失败: {str(e)}")
    
    async def send_info_reply(self, message: Message, content: str):
        """发送信息回复"""
        try:
            await message.reply(f"ℹ️ {content}")
        except Exception as e:
            logger.error(f"发送信息回复失败: {str(e)}")
    
    def parse_args(self, args_text: str) -> List[str]:
        """解析参数文本"""
        if not args_text:
            return []
        
        # 简单的参数解析，按空格分割
        return [arg.strip() for arg in args_text.split() if arg.strip()]
    
    async def safe_execute(self, message: Message, args: List[str]) -> Optional[str | bool]:
        """
        安全执行命令，包含异常处理
        
        Args:
            message: 消息对象
            args: 命令参数列表
            
        Returns:
            执行结果消息 (str) 如果 execute 方法返回字符串,
            True 如果命令已处理 (execute 运行完毕, 或参数验证失败, 或发生异常),
            None 如果命令未找到 (此情况由 CommandRegistry.execute_command 处理，safe_execute 本身不应返回 None)
        """
        try:
            # 验证参数
            if not self.validate_args(args):
                await self.send_error_reply(message, f"参数格式错误。正确用法: {self.get_usage()}")
                return True  # Indicate that the command was handled, albeit with an error
            
            # 执行命令
            # We don't care about the return value of execute() for signaling "handled" status,
            # only that it executed without raising an exception.
            await self.execute(message, args)
            return True # Indicate that the command was handled successfully
            
        except ValidationError as e:
            await self.send_error_reply(message, e.user_message)
            return True # Indicate that the command was handled, albeit with an error
        except TaimeiBotError as e:
            await self.send_error_reply(message, e.user_message)
            return True # Indicate that the command was handled, albeit with an error
        except Exception as e:
            log_error(logger, e, {
                'command': self.name,
                'args': args,
                'user_id': message.author_id,
                'channel_id': message.channel.id
            })
            await self.send_error_reply(message, "执行命令时发生未知错误，请稍后重试。")
            return True # Indicate that the command was handled, albeit with an error
    
    @abstractmethod
    def get_usage(self) -> str:
        """获取命令用法说明"""
        pass

class CommandRegistry:
    """命令注册表"""
    
    def __init__(self):
        self.commands: Dict[str, BaseCommand] = {}
        self.command_aliases: Dict[str, str] = {}
    
    def register(self, command: BaseCommand):
        """注册命令"""
        self.commands[command.name.lower()] = command
        
        # 注册别名
        for alias in command.aliases:
            self.command_aliases[alias.lower()] = command.name.lower()
    
    def unregister(self, command_name: str):
        """注销命令"""
        command_name = command_name.lower()
        if command_name in self.commands:
            command = self.commands[command_name]
            del self.commands[command_name]
            
            # 移除别名
            for alias in command.aliases:
                if alias.lower() in self.command_aliases:
                    del self.command_aliases[alias.lower()]
    
    def get_command(self, command_text: str) -> Optional[BaseCommand]:
        """获取命令对象"""
        command_text = command_text.lower().strip()
        
        # 直接匹配命令名
        if command_text in self.commands:
            return self.commands[command_text]
        
        # 匹配别名
        if command_text in self.command_aliases:
            command_name = self.command_aliases[command_text]
            return self.commands.get(command_name)
        
        return None
    
    def get_all_commands(self) -> List[BaseCommand]:
        """获取所有命令"""
        return list(self.commands.values())
    
    def set_context(self, bot: Bot, config: Dict[str, Any]):
        """为所有命令设置上下文"""
        for command in self.commands.values():
            command.set_context(bot, config)
    
    async def execute_command(self, command_text: str, message: Message, args: List[str]) -> Optional[str]:
        """执行命令"""
        command = self.get_command(command_text)
        if command is None:
            return None
        
        return await command.safe_execute(message, args)
    
    def get_help_text(self) -> str:
        """获取所有命令的帮助文本"""
        if not self.commands:
            return "暂无可用命令。"
        
        help_text = "**可用命令列表：**\n\n"
        for command in self.commands.values():
            help_text += f"• {command.get_help_text()}\n"
        
        return help_text
