from typing import Dict, Any
from .base import BaseTool, ToolResult
from services.memory import MemoryStore
from utils.logging_utils import get_logger

logger = get_logger(__name__)

MEMORY_SECTIONS = ["About the User", "Key Facts & Decisions", "Ongoing Context", "Past Interactions Summary"]


class ReadMemoryTool(BaseTool):

    def __init__(self):
        self.store = MemoryStore()

    @property
    def name(self) -> str:
        return "read_memory"

    @property
    def description(self) -> str:
        return "读取我的长期记忆。记忆按主题分为多个章节，包含用户信息、关键事实、当前上下文和历史摘要。每次对话开始时建议先读取记忆。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> ToolResult:
        try:
            content = self.store.read_memory()
            return ToolResult(success=True, data=content)
        except Exception as e:
            logger.error(f"Read memory failed: {e}")
            return ToolResult(success=False, error=f"读取记忆失败: {str(e)}")


class UpdateMemoryTool(BaseTool):

    def __init__(self):
        self.store = MemoryStore()

    @property
    def name(self) -> str:
        return "update_memory"

    @property
    def description(self) -> str:
        return "写入或更新长期记忆。你可以用这个工具来记住重要信息、用户偏好、决策等。内容会持久化保存。可选 sections: " + ", ".join(MEMORY_SECTIONS) + "，也可以创建新章节。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "记忆章节标题，例如 'About the User', 'Key Facts & Decisions'，或自定义新章节"
                },
                "content": {
                    "type": "string",
                    "description": "要记忆的内容"
                },
                "mode": {
                    "type": "string",
                    "enum": ["replace", "append"],
                    "description": "replace=替换该章节全部内容, append=追加新内容到章节末尾"
                }
            },
            "required": ["section", "content"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        section = kwargs.get('section', '')
        content = kwargs.get('content', '')
        mode = kwargs.get('mode', 'append')

        if not section or not content:
            return ToolResult(success=False, error="section 和 content 不能为空")

        try:
            ok = self.store.update_memory(section, content, mode)
            if ok:
                return ToolResult(success=True, data=f"记忆已更新: [{section}] ({mode})")
            else:
                return ToolResult(success=False, error="写入记忆失败")
        except Exception as e:
            logger.error(f"Update memory failed: {e}")
            return ToolResult(success=False, error=f"更新记忆失败: {str(e)}")
