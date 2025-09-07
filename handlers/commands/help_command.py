"""
帮助命令
提供命令帮助和使用说明
"""

from typing import List, Optional
from khl import Message, Bot
from .base_command import BaseCommand, CommandRegistry
from utils.logging_utils import get_logger
from utils.error_handler import ValidationError

logger = get_logger(__name__)

class HelpCommand(BaseCommand):
    """帮助命令"""
    
    def __init__(self):
        super().__init__(
            name="help",
            description="显示命令帮助信息",
            aliases=["帮助", "h", "?"],
        )
        self.command_registry: Optional[CommandRegistry] = None
    
    def set_command_registry(self, registry: CommandRegistry):
        """设置命令注册表"""
        self.command_registry = registry
    
    def validate_args(self, args: List[str]) -> bool:
        """验证命令参数"""
        # 帮助命令可以接受0个或1个参数
        if len(args) > 1:
            raise ValidationError("参数过多，帮助命令最多接受一个参数")
        
        return True
    
    async def execute(self, message: Message, args: List[str]) -> Optional[str]:
        """执行帮助命令"""
        if not self.command_registry:
            await self.send_error_reply(message, "命令系统未正确初始化")
            return None
        
        if not args:
            # 显示所有命令的帮助信息
            await self._show_all_commands_help(message)
        else:
            # 显示特定命令的详细帮助
            command_name = args[0].strip()
            await self._show_command_help(message, command_name)
        
        return None
    
    async def _show_all_commands_help(self, message: Message):
        """显示所有命令的帮助信息"""
        try:
            help_text = self.command_registry.get_help_text()
            
            # 添加额外信息
            help_text += "\n\n💡 **使用提示:**\n"
            help_text += "• 使用 `/help <命令名>` 查看特定命令的详细用法\n"
            help_text += "• 大部分命令支持中文别名，方便使用\n"
            help_text += "• 如有问题请联系管理员"
            
            await message.reply(help_text)
            
        except Exception as e:
            logger.error(f"显示帮助信息时发生错误: {str(e)}")
            await self.send_error_reply(message, "获取帮助信息时发生错误")
    
    async def _show_command_help(self, message: Message, command_name: str):
        """显示特定命令的详细帮助"""
        try:
            command = self.command_registry.get_command(command_name)
            
            if command is None:
                await self.send_error_reply(message, f"未找到命令 '{command_name}'，使用 `/help` 查看所有可用命令")
                return
            
            # 构建详细帮助信息
            help_text = f"📖 **命令详情: {command.name}**\n\n"
            help_text += f"**描述:** {command.description}\n\n"
            help_text += f"**用法:**\n```\n{command.get_usage()}\n```\n\n"
            
            if command.aliases:
                help_text += f"**别名:** {', '.join(command.aliases)}\n\n"
            
            # 添加使用示例
            help_text += "**使用示例:**\n"
            examples = self._get_command_examples(command.name)
            for example in examples:
                help_text += f"• `{example}`\n"
            
            help_text += "\n💡 **提示:** 使用命令时请确保参数格式正确"
            
            await message.reply(help_text)
            
        except Exception as e:
            logger.error(f"显示命令详情时发生错误: {str(e)}")
            await self.send_error_reply(message, f"获取命令 '{command_name}' 的帮助信息时发生错误")
    
    def _get_command_examples(self, command_name: str) -> List[str]:
        """获取命令使用示例"""
        examples = {
            "tf": [
                "/tf ms",
                "/tf 恶魔学识", 
                "/天赋 冰霜",
                "/tx 恢复"
            ],
            "tr": [
                "/tr Hello World",
                "/tr 你好世界",
                "/翻译 How are you?",
                "/fy 谢谢"
            ],
            "ai": [
                "/ai 你好",
                "/ai 今天天气怎么样？",
                "/聊天 推荐一本书",
                "/chat 什么是机器学习？"
            ],
            "help": [
                "/help",
                "/help tf",
                "/帮助 tr"
            ]
        }
        
        return examples.get(command_name, [f"/{command_name} <参数>"])
    
    def get_usage(self) -> str:
        """获取命令用法说明"""
        return f"{self.name} [命令名]\n例如: {self.name} 或 {self.name} talent"
    
    async def send_welcome_message(self, message: Message):
        """发送欢迎消息"""
        welcome_text = """
👋 **欢迎使用 TaimeiBot！**

我是一个功能丰富的魔兽世界机器人，目前支持以下功能：

🎯 **主要功能:**
• **天赋查询** - 查询魔兽世界职业专精天赋配置
• **文本翻译** - 中英文互译功能  
• **AI聊天** - 与AI助手进行智能对话
• **帮助系统** - 提供详细的命令使用帮助

📝 **快速开始:**
• 输入 `/help` 查看所有可用命令
• 输入 `/help <命令名>` 查看特定命令的详细用法
• 大部分命令支持中文别名，方便使用

🔧 **提示:**
• 请确保在正确的频道使用相应功能
• 如有问题请联系管理员
        """
        
        try:
            await message.reply(welcome_text)
        except Exception as e:
            logger.error(f"发送欢迎消息时发生错误: {str(e)}")
    
    async def send_command_list(self, message: Message, category: str = "all"):
        """发送分类命令列表"""
        if not self.command_registry:
            await self.send_error_reply(message, "命令系统未正确初始化")
            return
        
        try:
            commands = self.command_registry.get_all_commands()
            
            # 按功能分类命令
            categories = {
                "game": ["talent"],
                "utility": ["translate", "help"],
                "ai": ["chat"],
                "all": [cmd.name for cmd in commands]
            }
            
            if category not in categories:
                category = "all"
            
            category_names = {
                "game": "🎮 游戏功能",
                "utility": "🛠️ 实用工具", 
                "ai": "🤖 AI功能",
                "all": "📋 所有功能"
            }
            
            text = f"{category_names[category]}\n\n"
            
            for cmd_name in categories[category]:
                command = self.command_registry.get_command(cmd_name)
                if command:
                    text += f"• **{command.name}** - {command.description}\n"
            
            if category != "all":
                text += f"\n输入 `/help` 查看所有命令，或使用 `/help <命令名>` 查看详细用法"
            
            await message.reply(text)
            
        except Exception as e:
            logger.error(f"发送命令列表时发生错误: {str(e)}")
            await self.send_error_reply(message, "获取命令列表时发生错误")
    
    async def check_command_exists(self, command_name: str) -> bool:
        """检查命令是否存在"""
        if not self.command_registry:
            return False
        
        return self.command_registry.get_command(command_name) is not None
    
    async def get_command_stats(self) -> dict:
        """获取命令统计信息"""
        if not self.command_registry:
            return {"total": 0, "categories": {}}
        
        commands = self.command_registry.get_all_commands()
        
        stats = {
            "total": len(commands),
            "categories": {
                "game": 0,
                "utility": 0,
                "ai": 0
            }
        }
        
        game_commands = ["talent"]
        utility_commands = ["translate", "help"]
        ai_commands = ["chat"]
        
        for command in commands:
            if command.name in game_commands:
                stats["categories"]["game"] += 1
            elif command.name in utility_commands:
                stats["categories"]["utility"] += 1
            elif command.name in ai_commands:
                stats["categories"]["ai"] += 1
        
        return stats
