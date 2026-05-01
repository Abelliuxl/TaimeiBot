import aiohttp
from typing import Dict, Any
from .base import BaseTool, ToolResult
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class FetchURLTool(BaseTool):

    @property
    def name(self) -> str:
        return "fetch_url"

    @property
    def description(self) -> str:
        return "直接通过HTTP GET请求获取指定URL的原始内容（JSON/HTML/纯文本）。适合调用API接口或获取不需要JavaScript渲染的页面。比浏览器更快、更轻量。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要获取的URL，例如 https://api.example.com/data"
                }
            },
            "required": ["url"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get('url', '')
        if not url:
            return ToolResult(success=False, error="URL不能为空")
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            content = await self._fetch(url)
            return ToolResult(success=True, data=content)
        except Exception as e:
            logger.error(f"Fetch URL failed: {e}")
            return ToolResult(success=False, error=f"获取URL失败: {str(e)}")

    async def _fetch(self, url: str, timeout: int = 15) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                content_type = resp.headers.get("Content-Type", "")
                text = await resp.text()

                if "application/json" in content_type or url.endswith(".json"):
                    import json
                    parsed = json.loads(text)
                    return json.dumps(parsed, ensure_ascii=False, indent=2)[:8000]

                return text.strip()[:8000]
