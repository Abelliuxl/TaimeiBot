import os
import json
import datetime
from typing import List, Optional
from utils.logging_utils import get_logger

logger = get_logger(__name__)

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "memory")
MEMORY_FILE = os.path.join(MEMORY_DIR, "agent_memory.md")
CONVERSATION_LOG = os.path.join(MEMORY_DIR, "conversations.jsonl")
MAX_CONVERSATIONS_BEFORE_HEARTBEAT = 20


class MemoryStore:

    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        if not os.path.exists(MEMORY_FILE):
            self._init_memory_file()

    def _init_memory_file(self):
        content = """# Agent Memory

## About the User
*（用户信息、偏好等，由 agent 自动维护）*

## Key Facts & Decisions
*（重要的事实、已做的决定、项目背景等）*

## Ongoing Context
*（当前正在处理的事情、待办等）*

## Past Interactions Summary
*（历史对话摘要，由心跳自动整理）*
"""
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("记忆文件已初始化")

    def read_memory(self) -> str:
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取记忆失败: {e}")
            return "（读取记忆失败）"

    def update_memory(self, section: str, content: str, mode: str = "replace") -> bool:
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"读取记忆文件失败: {e}")
            return False

        lines = text.split('\n')
        section_header = f"## {section}"
        header_idx = None
        next_header_idx = len(lines)

        for i, line in enumerate(lines):
            if line.strip() == section_header:
                header_idx = i
            elif header_idx is not None and line.strip().startswith('## '):
                next_header_idx = i
                break

        if header_idx is None:
            lines.append("")
            lines.append(section_header)
            lines.append("")
            lines.append(content)
        elif mode == "replace":
            before = lines[:header_idx + 1]
            after = lines[next_header_idx:]
            body = [""] + content.split('\n')
            lines = before + body + after
        else:
            indent = ""
            for ch in content.split('\n')[0]:
                if ch in ('- ', '* '):
                    indent = ch
                    break
            body_lines = content.strip().split('\n')
            insert_pos = next_header_idx
            lines[insert_pos:insert_pos] = body_lines

        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            logger.info(f"记忆已更新: section={section}, mode={mode}")
            return True
        except Exception as e:
            logger.error(f"写入记忆失败: {e}")
            return False

    def log_conversation(self, user_msg: str, agent_reply: str, tools_used: Optional[list] = None):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user_msg[:500],
            "reply": agent_reply[:500],
            "tools": tools_used or [],
        }
        try:
            with open(CONVERSATION_LOG, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"记录对话失败: {e}")

    def get_recent_conversations(self, count: int = 20) -> List[dict]:
        try:
            if not os.path.exists(CONVERSATION_LOG):
                return []
            with open(CONVERSATION_LOG, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            entries = [json.loads(l) for l in lines if l.strip()]
            return entries[-count:]
        except Exception as e:
            logger.error(f"读取对话记录失败: {e}")
            return []

    def clear_conversation_log(self):
        try:
            open(CONVERSATION_LOG, 'w').close()
        except Exception as e:
            logger.error(f"清理对话记录失败: {e}")

    def should_run_heartbeat(self) -> bool:
        try:
            if not os.path.exists(CONVERSATION_LOG):
                return False
            with open(CONVERSATION_LOG, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
            return count >= MAX_CONVERSATIONS_BEFORE_HEARTBEAT
        except Exception:
            return False
