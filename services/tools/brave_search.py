import aiohttp
from typing import Dict, Any
from .base import BaseTool, ToolResult
from .proxy import get_proxy
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class BraveSearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "brave_search"

    @property
    def description(self) -> str:
        return "使用 Brave 搜索引擎搜索互联网。返回相关网页标题、摘要和链接。适合快速查找资料、获取多样化信息来源。"

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
            return ToolResult(success=False, error="Brave Search API key 未配置，请联系管理员设置")

        try:
            results = await self._search_brave(query, api_key)
            return ToolResult(success=True, data=results)
        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return ToolResult(success=False, error=f"Brave 搜索失败: {str(e)}")

    def _get_api_key(self) -> str | None:
        import os
        key = os.environ.get("BRAVE_SEARCH_API_KEY")
        if key:
            return key
        try:
            import json
            with open(self._config_path(), 'r') as f:
                cfg = json.load(f)
            return cfg.get("brave_api_key")
        except Exception:
            return None

    def _config_path(self):
        import os
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "config.json")

    async def _search_brave(self, query: str, api_key: str) -> str:
        url = "https://api.search.brave.com/res/v1/web/search"
        params = {"q": query, "count": 8}
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        proxy = get_proxy()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=proxy,
                                    timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    raise Exception(f"Brave returned {resp.status}")
                data = await resp.json()

        parts = [f"搜索: {query}\n"]
        results = data.get("web", {}).get("results", [])
        for i, r in enumerate(results[:8], 1):
            parts.append(f"{i}. {r.get('title', '')}")
            desc = r.get('description', '')
            if desc:
                parts.append(f"   {desc[:200]}")
            parts.append(f"   {r.get('url', '')}\n")

        if len(parts) == 1:
            parts.append("（未找到相关结果）")

        return "\n".join(parts)
