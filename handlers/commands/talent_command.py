"""
天赋查询命令
处理魔兽世界天赋查询相关的命令
"""

from typing import List, Optional
from khl import Message, Bot
from .base_command import BaseCommand
from services.raider_service import fetch_talent_loadouts
from services.data import GameDataRepository
from utils.logging_utils import get_logger
from utils.error_handler import ValidationError
import os

logger = get_logger(__name__)

class TalentCommand(BaseCommand):
    """天赋查询命令"""
    
    def __init__(self):
        super().__init__(
            name="tf",
            description="查询魔兽世界职业专精天赋配置",
            aliases=["天赋", "tx", "t", "talent"]
        )
        self.game_data_repo: Optional[GameDataRepository] = None
    
    def set_context(self, bot: Bot, config: dict):
        """设置命令执行上下文"""
        super().set_context(bot, config)
        # 初始化游戏数据仓库
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))  # 获取项目根目录
        self.game_data_repo = GameDataRepository(base_dir)
    
    def validate_args(self, args: List[str]) -> bool:
        """验证命令参数"""
        if not args:
            raise ValidationError("请提供要查询的职业专精简称")
        
        if len(args) > 1:
            raise ValidationError("参数过多，请提供一个职业专精简称")
        
        return True
    
    async def execute(self, message: Message, args: List[str]) -> Optional[str]:
        """执行天赋查询命令"""
        spec_simple = args[0].strip()
        
        # 检查功能开关
        if not self.config.get('enable_talent_query', True):
            await self.send_error_reply(message, "天赋查询功能当前已禁用")
            return None
        
        try:
            # 查询天赋信息
            logger.info(f"用户 {message.author_id} 查询天赋: {spec_simple}")
            
            # 调用raider服务获取天赋信息
            talent_info = await fetch_talent_loadouts(spec_simple)
            
            if talent_info is None:
                await self.send_error_reply(message, f"未找到职业专精 '{spec_simple}' 的天赋信息，请检查简称是否正确")
                return None
            
            # 发送天赋信息
            await message.reply(talent_info)
            return None
            
        except Exception as e:
            logger.error(f"查询天赋时发生错误: {str(e)}")
            await self.send_error_reply(message, "查询天赋时发生错误，请稍后重试")
            return None
    
    def get_usage(self) -> str:
        """获取命令用法说明"""
        return f"{self.name} <职业专精简称>\n例如: {self.name} 恶魔学识 或 {self.name} ms"
    
    async def get_talent_suggestions(self, partial_spec: str) -> List[str]:
        """获取天赋建议（用于自动补全）"""
        if not self.game_data_repo:
            return []
        
        try:
            suggestions = []
            class_spec_data = self.game_data_repo.get_class_spec_data()
            partial_spec = partial_spec.lower()
            
            for class_name, specs in class_spec_data.items():
                for spec, abbreviations in specs.items():
                    for abbr in abbreviations:
                        if abbr.lower().startswith(partial_spec):
                            suggestions.append(abbr)
            
            return suggestions[:10]  # 返回前10个建议
            
        except Exception as e:
            logger.error(f"获取天赋建议时发生错误: {str(e)}")
            return []
    
    async def send_available_specs(self, message: Message):
        """发送可用的职业专精列表"""
        if not self.game_data_repo:
            await self.send_error_reply(message, "无法获取职业专精数据")
            return
        
        try:
            class_spec_data = self.game_data_repo.get_class_spec_data()
            specs_text = "**可用职业专精简称列表：**\n\n"
            
            for class_name, specs in class_spec_data.items():
                specs_text += f"**{class_name}**: "
                spec_list = []
                for spec, abbreviations in specs.items():
                    spec_list.append(f"{spec}({', '.join(abbreviations)})")
                specs_text += ", ".join(spec_list) + "\n"
            
            # 如果消息太长，分批发送
            if len(specs_text) > 2000:
                # 分割消息
                lines = specs_text.split('\n')
                current_chunk = "**可用职业专精简称列表：**\n\n"
                
                for line in lines[2:]:  # 跳过标题行
                    if len(current_chunk + line + '\n') > 1900:
                        await message.reply(current_chunk)
                        current_chunk = ""
                    current_chunk += line + '\n'
                
                if current_chunk.strip():
                    await message.reply(current_chunk)
            else:
                await message.reply(specs_text)
                
        except Exception as e:
            logger.error(f"发送职业专精列表时发生错误: {str(e)}")
            await self.send_error_reply(message, "获取职业专精列表时发生错误")
