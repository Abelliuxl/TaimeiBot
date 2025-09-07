"""
命令处理模块
实现命令模式，将消息处理逻辑模块化
"""

from .base_command import BaseCommand, CommandRegistry
from .talent_command import TalentCommand
# from .translation_command import TranslationCommand # Removed
# from .ai_chat_command import AIChatCommand # Removed
from .help_command import HelpCommand

__all__ = [
    'BaseCommand',
    'CommandRegistry',
    'TalentCommand', 
    # 'TranslationCommand', # Removed
    # 'AIChatCommand', # Removed
    'HelpCommand'
]
