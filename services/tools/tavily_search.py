import aiohttp
from typing import Dict, Any
from .base import BaseTool, ToolResult
from .proxy import get_proxy
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class TavilySearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return "使用 Tavily 搜索引擎搜索互联网。返回高质量的相关网页标题、摘要和来源链接。适合深度研究、需要高准确性信息的场景。"

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

        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="Tavily API key 未配置，请联系管理员设置")

        try:
            results = await self._search_tavily(query, api_key)
            return ToolResult(success=True, data=results)
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return ToolResult(success=False, error=f"Tavily 搜索失败: {str(e)}")

    def _get_api_key(self) -> str | None:
        import os
        key = os.environ.get("TAVILY_API_KEY")
        if key:
            return key
        try:
            import json
            with open(self._config_path(), 'r') as f:
                cfg = json.load(f)
            return cfg.get("tavily_api_key")
        except Exception:
            return None

    def _config_path(self):
        import os
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "config.json")

    async def _search_tavily(self, query: str, api_key: str) -> str:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 8,
            "include_answer": True,
        }
        proxy = get_proxy()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, proxy=proxy,
                                    timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    raise Exception(f"Tavily returned {resp.status}")
                data = await resp.json()

        parts = [f"搜索: {query}\n"]
        answer = data.get("answer", "")
        if answer:
            parts.append(f"概述: {answer}\n")

        results = data.get("results", [])
        for i, r in enumerate(results[:8], 1):
            parts.append(f"{i}. {r.get('title', '')}")
            content = r.get('content', '')
            if content:
                parts.append(f"   {content[:200]}")
            parts.append(f"   {r.get('url', '')}\n")

        if len(parts) == 1:
            parts.append("（未找到相关结果）")

        return "\n".join(parts)
