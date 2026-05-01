from typing import Dict, Any
from .base import BaseTool, ToolResult
from services.raider_service import fetch_talent_loadouts as _fetch_talent_loadouts
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class TalentLookupTool(BaseTool):

    @property
    def name(self) -> str:
        return "talent_lookup"

    @property
    def description(self) -> str:
        return "查询魔兽世界职业专精的天赋配置。根据用户提供的职业专精名称或简称，从 raider.io 获取前列玩家的天赋代码。返回格式化结果。用法举例：惩戒骑、retribution paladin、浩劫 dh、恶魔学识、ms、bdk"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "string",
                    "description": "职业专精名称或简称，如 惩戒骑、retribution、浩劫、恶魔学识、ms、bdk、冰dk"
                }
            },
            "required": ["spec"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        spec = kwargs.get('spec', '').strip().lower()
        if not spec:
            return ToolResult(success=False, error="请提供职业专精名称或简称")

        try:
            result = await _fetch_talent_loadouts(spec)
            if result is None:
                return ToolResult(success=False, data=f"未找到 '{spec}' 的天赋信息，请检查简称是否正确")
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error(f"Talent lookup failed: {e}")
            return ToolResult(success=False, error=f"查询天赋失败: {str(e)}")
