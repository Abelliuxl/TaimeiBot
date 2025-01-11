import aiohttp
import json
from typing import Any, Dict, Optional
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)

async def make_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """发送HTTP请求"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data if method in ['POST', 'PUT', 'PATCH'] else None
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API请求失败: {str(e)}")
            raise 