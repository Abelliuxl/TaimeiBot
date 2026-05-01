import aiohttp
import os
from typing import Dict, Any, Optional
from .base import BaseTool, ToolResult
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def _get_proxy() -> Optional[str]:
    return os.environ.get("https_proxy") or os.environ.get("http_proxy") or None


class WebSearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "搜索互联网获取最新信息。返回相关网页摘要和链接。适合初步查找资料、了解当前事件。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get('query', '')
        if not query:
            return ToolResult(success=False, error="搜索关键词不能为空")

        try:
            results = await self._search_duckduckgo(query)
            return ToolResult(success=True, data=results)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(success=False, error=f"搜索失败: {str(e)}")

    async def _search_duckduckgo(self, query: str) -> str:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        proxy = _get_proxy()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, proxy=proxy, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    raise Exception(f"DuckDuckGo returned {resp.status}")
                data = await resp.json()

        parts = []

        abstract = data.get("AbstractText", "")
        if abstract:
            source = data.get("AbstractSource", "")
            parts.append(f"[{source}] {abstract}")

        answer = data.get("Answer", "")
        if answer:
            parts.append(f"答案: {answer}")

        definition = data.get("Definition", "")
        if definition:
            parts.append(f"定义: {definition}")

        related = data.get("RelatedTopics", [])
        if related:
            parts.append("\n相关结果:")
            count = 0
            for item in related:
                if count >= 8:
                    break
                if "Text" in item:
                    parts.append(f"  - {item['Text']}")
                    count += 1
                elif "Topics" in item:
                    for sub in item["Topics"]:
                        if count >= 8:
                            break
                        if "Text" in sub:
                            parts.append(f"  - {sub['Text']}")
                            count += 1

        if not parts:
            parts.append(f"未找到 '{query}' 的相关结果")

        return "\n".join(parts)
