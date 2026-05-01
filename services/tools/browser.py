import asyncio
from typing import Dict, Any
from .base import BaseTool, ToolResult
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class BrowseWebpageTool(BaseTool):

    @property
    def name(self) -> str:
        return "browse_webpage"

    @property
    def description(self) -> str:
        return "使用浏览器打开一个网页，获取完整的页面文本内容（包含JavaScript渲染后的内容）。适合查看新闻文章、博客、文档等详细页面内容。输入应为完整URL（含 https://）。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要访问的网页完整URL，例如 https://example.com/page"
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
            content = await self._browse(url)
            return ToolResult(success=True, data=content)
        except Exception as e:
            logger.error(f"Browse webpage failed: {e}")
            return ToolResult(success=False, error=f"浏览网页失败: {str(e)}")

    async def _browse(self, url: str, timeout_ms: int = 30000) -> str:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.wait_for_timeout(2000)

                title = await page.title()
                text = await page.evaluate("document.body.innerText")
                current_url = page.url

                result = f"标题: {title}\n页面URL: {current_url}\n\n{text.strip()[:8000]}"
                return result
            finally:
                await browser.close()
