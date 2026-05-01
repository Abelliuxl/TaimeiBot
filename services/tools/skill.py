import os
from typing import Dict, Any, List
from .base import BaseTool, ToolResult
from utils.logging_utils import get_logger

logger = get_logger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "skills")


def _load_skills() -> List[dict]:
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for fname in sorted(os.listdir(SKILLS_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(SKILLS_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"读取技能文件失败 {fname}: {e}")
            continue

        meta = {}
        body = content
        if content.startswith('---'):
            import yaml
            parts = content.split('---', 2)
            if len(parts) >= 3:
                meta = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            elif len(parts) == 2:
                meta = yaml.safe_load(parts[1]) or {}

        skills.append({
            "name": meta.get("name", fname.replace(".md", "")),
            "description": meta.get("description", ""),
            "workflow": meta.get("workflow", body),
            "file": fname,
        })
    return skills


class ListSkillsTool(BaseTool):

    @property
    def name(self) -> str:
        return "list_skills"

    @property
    def description(self) -> str:
        return "列出所有可用的技能。技能是预定义的工作流模板，可以帮你更高效地完成特定类型的任务。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> ToolResult:
        skills = _load_skills()
        if not skills:
            return ToolResult(success=True, data="当前没有可用技能。")
        lines = ["可用技能:\n"]
        for s in skills:
            lines.append(f"- **{s['name']}**: {s['description']}")
        return ToolResult(success=True, data="\n".join(lines))


class LoadSkillTool(BaseTool):

    @property
    def name(self) -> str:
        return "load_skill"

    @property
    def description(self) -> str:
        return "加载指定技能的工作流指令。技能是一组预定义的操作步骤，会指导你如何完成特定类型的任务。先用 list_skills 查看可用技能。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "技能名称（对应 list_skills 中的 name）"
                }
            },
            "required": ["name"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        target = kwargs.get('name', '').strip().lower()
        if not target:
            return ToolResult(success=False, error="技能名称不能为空")

        skills = _load_skills()
        for s in skills:
            if s['name'].lower() == target:
                return ToolResult(success=True, data=s['workflow'])

        names = [s['name'] for s in skills]
        return ToolResult(success=False,
                          error=f"未找到技能 '{target}'。可用技能: {', '.join(names) if names else '无'}")


class WriteSkillTool(BaseTool):

    @property
    def name(self) -> str:
        return "write_skill"

    @property
    def description(self) -> str:
        return "创建或更新一个技能。技能是 YAML 格式的 .md 文件，包含 name、description 和 workflow 字段。如果技能名已存在则会覆盖。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "技能名称（英文短名，如 wow_version_check）"
                },
                "description": {
                    "type": "string",
                    "description": "技能描述，说明这个技能用来做什么"
                },
                "workflow": {
                    "type": "string",
                    "description": "技能的工作流步骤，每一步一行，用数字编号"
                }
            },
            "required": ["name", "description", "workflow"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get('name', '').strip()
        description = kwargs.get('description', '').strip()
        workflow = kwargs.get('workflow', '').strip()

        if not name or not description or not workflow:
            return ToolResult(success=False, error="name、description、workflow 都不能为空")

        safe_name = name.lower().replace(' ', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')
        if not safe_name:
            return ToolResult(success=False, error="技能名称只支持字母、数字、下划线和短横")

        fpath = os.path.join(SKILLS_DIR, f"{safe_name}.md")
        content = f"""---
name: {safe_name}
description: {description}
workflow: |
  {workflow.replace(chr(10), chr(10) + '  ')}
---
"""
        try:
            os.makedirs(SKILLS_DIR, exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"技能已保存: {safe_name}")
            return ToolResult(success=True, data=f"技能 '{safe_name}' 已{'更新' if os.path.exists(fpath) else '创建'}")
        except Exception as e:
            logger.error(f"保存技能失败: {e}")
            return ToolResult(success=False, error=f"保存技能失败: {str(e)}")


class DeleteSkillTool(BaseTool):

    @property
    def name(self) -> str:
        return "delete_skill"

    @property
    def description(self) -> str:
        return "删除一个技能。注意此操作不可撤销，请确认后再执行。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "要删除的技能名称（对应 list_skills 中的 name）"
                }
            },
            "required": ["name"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        target = kwargs.get('name', '').strip().lower()
        if not target:
            return ToolResult(success=False, error="技能名称不能为空")

        skills = _load_skills()
        for s in skills:
            if s['name'].lower() == target:
                try:
                    os.remove(os.path.join(SKILLS_DIR, s['file']))
                    logger.info(f"技能已删除: {s['name']}")
                    return ToolResult(success=True, data=f"技能 '{s['name']}' 已删除")
                except Exception as e:
                    return ToolResult(success=False, error=f"删除失败: {str(e)}")

        return ToolResult(success=False, error=f"未找到技能 '{target}'")
