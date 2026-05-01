import os
from typing import Dict, Any, List
from .base import BaseTool, ToolResult
from utils.logging_utils import get_logger

logger = get_logger(__name__)

ALLOWED_PATHS: List[str] = [
    "/home/liuxl/TaimeiBot/skills/",
]

ALLOWED_FILE_PATTERNS: List[str] = [
    ".json",
    ".txt",
    ".py",
    ".toml",
]


class FileReaderTool(BaseTool):

    @property
    def name(self) -> str:
        return "read_local_file"

    @property
    def description(self) -> str:
        return "读取本地文件内容。目前无可访问目录，需管理员配置后可读取json/txt/py/toml格式文件。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径（相对项目根目录或绝对路径），如 config/constants.py"
                }
            },
            "required": ["file_path"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get('file_path', '')
        if not file_path:
            return ToolResult(success=False, error="文件路径不能为空")

        resolved = self._resolve_path(file_path)
        if resolved is None:
            return ToolResult(success=False,
                              error=f"无权访问该文件。允许的目录: {', '.join(ALLOWED_PATHS)}")

        if not os.path.isfile(resolved):
            return ToolResult(success=False, error=f"文件不存在: {file_path}")

        ext = os.path.splitext(resolved)[1].lower()
        if ext not in ALLOWED_FILE_PATTERNS and ext != '':
            return ToolResult(success=False, error=f"不支持的文件类型: {ext}")

        try:
            with open(resolved, 'r', encoding='utf-8') as f:
                content = f.read()
            return ToolResult(success=True, data=content)
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return ToolResult(success=False, error=f"读取文件失败: {str(e)}")

    def _resolve_path(self, file_path: str) -> str | None:
        if file_path.startswith('/'):
            candidate = os.path.normpath(file_path)
        else:
            candidate = os.path.normpath(os.path.join("/home/liuxl/TaimeiBot", file_path))

        for allowed in ALLOWED_PATHS:
            allowed_norm = os.path.normpath(allowed)
            if candidate.startswith(allowed_norm):
                return candidate
            if os.path.realpath(candidate).startswith(os.path.realpath(allowed_norm)):
                return candidate

        return None
