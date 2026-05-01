import asyncio
import datetime
from typing import Optional
from services.memory import MemoryStore
from services.llm_service import LLMService
from utils.logging_utils import get_logger

logger = get_logger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 1800

HEARTBEAT_PROMPT = """你是一个记忆整理助手。请阅读以下最近的对话记录，分析并更新长期记忆文件。

## 你的任务
1. 阅读当前记忆和最近对话
2. 提取新的重要信息：用户偏好、决定、事实、进行中的任务
3. 按章节整理输出

## 输出格式
请严格按照以下格式输出（每个章节可选，不需要更新的章节可以留空）：

===About the User===
这里写关于用户的新信息

===Key Facts & Decisions===
这里写新的事实和决策

===Ongoing Context===
这里写当前上下文更新

===Past Interactions Summary===
这里写对最近对话的简要摘要

如果某个章节不需要更新，输出 ===SectionName=== 后留空即可。"""


class HeartbeatService:

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.store = MemoryStore()
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"记忆心跳已启动 (间隔 {HEARTBEAT_INTERVAL_SECONDS}s)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("记忆心跳已停止")

    async def heartbeat_once(self):
        try:
            current_memory = self.store.read_memory()
            recent = self.store.get_recent_conversations(20)

            if not recent:
                logger.debug("心跳: 无新对话")
                return

            conversations_text = ""
            for i, c in enumerate(recent, 1):
                conversations_text += f"\n--- 对话 {i} ---\n用户: {c.get('user', '')}\n太美: {c.get('reply', '')}\n工具: {', '.join(c.get('tools', []))}\n"

            prompt = f"""当前记忆：
{current_memory}

最近对话记录：
{conversations_text}

{HEARTBEAT_PROMPT}"""

            logger.info("心跳: 正在分析对话并整理记忆...")
            response = await self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                thinking=True,
                max_tokens=16000,
            )

            result = response['choices'][0]['message'].get('content', '').strip()
            if not result:
                logger.warning("心跳: LLM 返回为空")
                return

            self._parse_and_update_memory(result)
            self.store.clear_conversation_log()
            logger.info("心跳: 记忆整理完成")

        except Exception as e:
            logger.error(f"心跳执行失败: {e}")

    def _parse_and_update_memory(self, text: str):
        import re
        pattern = r'===(.+?)===\s*(.*?)(?=\n===|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)

        updated = False
        for section, content in matches:
            content = content.strip()
            if content:
                self.store.update_memory(section.strip(), content, mode="append")
                updated = True

        if not updated:
            if "Past Interactions Summary" not in text:
                self.store.update_memory("Past Interactions Summary",
                                         f"[{datetime.date.today().isoformat()}] 心跳运行但未提取到新信息",
                                         mode="append")

    async def _heartbeat_loop(self):
        while self._running:
            try:
                if self.store.should_run_heartbeat():
                    await self.heartbeat_once()
                else:
                    logger.debug(f"心跳: 对话数未达阈值，跳过")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环异常: {e}")

            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
