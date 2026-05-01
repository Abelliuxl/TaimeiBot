from typing import Dict, Any, List
import json
from services.llm_service import LLMService
from services.tools import (
    BaseTool, WebSearchTool, BrowseWebpageTool, FetchURLTool, FileReaderTool,
)
from utils.logging_utils import get_logger
from utils.error_handler import log_error

logger = get_logger(__name__)

AGENT_SYSTEM_PROMPT = """你是一个智能 AI 助手，名叫"太美"。你可以使用多种工具来获取信息。

## 工作流程
1. 分析用户的问题，制定计划
2. 按需调用工具获取信息
3. 根据结果进一步分析或补充查询
4. 汇总所有信息，给出完整、清晰的回答

## 可用工具
- **web_search**: 搜索互联网（关键词搜索，返回摘要）。适合找资料、了解当前事件。
- **browse_webpage**: 用浏览器打开网页（支持JS渲染）。适合看新闻文章、博客、文档详情。
- **fetch_url**: 直接HTTP获取URL内容。适合调用API接口。
- **read_local_file**: 读取本地文件（config/ 和 raider_data/ 目录下）。

## 使用策略
- 先用 web_search 搜索找到相关资源
- 然后用 browse_webpage 或 fetch_url 获取具体内容
- 如果需要本地数据，用 read_local_file
- 返回给用户的内容要整理好，不要直接丢原始数据"""


class AgentService:

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()

    def _register_tools(self):
        for tool in [WebSearchTool(), BrowseWebpageTool(), FetchURLTool(), FileReaderTool()]:
            self.tools[tool.name] = tool

    async def run(self, user_message: str, max_tool_rounds: int = 8) -> str:
        messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        tool_defs = [t.to_openai_tool() for t in self.tools.values()]

        for _ in range(max_tool_rounds):
            try:
                response = await self.llm_service.chat(
                    messages,
                    tools=tool_defs,
                    tool_choice="auto",
                    thinking=True,
                    max_tokens=128000,
                )
            except Exception as e:
                log_error(logger, e, {})
                raise

            choice = response['choices'][0]
            msg = choice['message']
            finish = choice.get('finish_reason', '')

            assistant_msg = {"role": "assistant", "content": msg.get('content') or ""}
            if msg.get('tool_calls'):
                assistant_msg["tool_calls"] = msg['tool_calls']
            messages.append(assistant_msg)

            if finish == 'stop' or not msg.get('tool_calls'):
                final = msg.get('content', '')
                return final.strip() if final else "抱歉，我没有生成有效回复。"

            for tc in msg['tool_calls']:
                tool_name = tc['function']['name']
                try:
                    raw_args = tc['function']['arguments']
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception as e:
                    result_str = f"参数解析失败: {str(e)}"
                else:
                    tool = self.tools.get(tool_name)
                    if tool:
                        tool_result = await tool.execute(**args)
                        result_str = str(tool_result.data) if tool_result.success else f"错误: {tool_result.error}"
                    else:
                        result_str = f"未知工具: {tool_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc['id'],
                    "content": result_str,
                })

        messages.append({
            "role": "user",
            "content": "请基于以上所有工具调用的结果，给出最终的回答。如果没有获取到有用信息，请如实告知用户。"
        })

        try:
            final_response = await self.llm_service.chat(messages, thinking=True, max_tokens=128000)
            content = final_response['choices'][0]['message'].get('content', '')
            return content.strip() if content else "达到最大工具调用次数，请重试。"
        except Exception as e:
            log_error(logger, e, {'stage': 'final_summary'})
            return "处理超时，请稍后重试。"
