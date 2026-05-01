import aiohttp
import json
import os
from typing import Dict, Any, Optional, List
from utils.logging_utils import get_logger
from utils.error_handler import APIError, NetworkError, ConfigError, log_error
from utils.retry_decorator import retry, get_default_retry_config
from config.constants import AI_CHAT_CONFIG
from services.data.config_repository import ConfigRepository

logger = get_logger(__name__)

class LLMService:
    """大语言模型服务类"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        bot_config = config_manager.get_bot_config()
        self.api_url = bot_config.get('llm_api_url')
        self.api_key = bot_config.get('llm_api_key')
        self.default_model = bot_config.get('llm_model', 'deepseek-v4-flash')
        self.default_thinking = bot_config.get('thinking', AI_CHAT_CONFIG.get('thinking', {"type": "enabled", "reasoning_effort": "max"}))
        self.default_max_tokens = bot_config.get('max_tokens', 65536)

        if not self.api_url or not self.api_key:
            raise ConfigError("LLM服务配置不完整，缺少API URL或API密钥")

        logger.info("LLM服务初始化完成")

    @retry(**get_default_retry_config().__dict__)
    async def _make_api_request(self, messages: list, **kwargs) -> Dict[str, Any]:
        """发送API请求的通用方法"""
        data = {
            "model": kwargs.get('model', self.default_model),
            "messages": messages,
        }

        if 'temperature' in kwargs:
            data['temperature'] = kwargs['temperature']
        if 'max_tokens' in kwargs:
            data['max_tokens'] = kwargs['max_tokens']
        else:
            data['max_tokens'] = self.default_max_tokens

        if 'thinking' in kwargs:
            t = kwargs['thinking']
            if t is True:
                data['thinking'] = {"type": "enabled", "reasoning_effort": "max"}
                data['max_tokens'] = max(data.get('max_tokens', 65536), 128000)
            elif isinstance(t, dict):
                data['thinking'] = t
                if t.get('reasoning_effort') == 'max':
                    data['max_tokens'] = max(data.get('max_tokens', 65536), 128000)

        if 'tools' in kwargs and kwargs['tools']:
            data['tools'] = kwargs['tools']
        if 'tool_choice' in kwargs:
            data['tool_choice'] = kwargs['tool_choice']

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'choices' not in result or not result['choices']:
                            raise APIError("API响应格式错误：缺少choices字段")
                        if 'message' not in result['choices'][0]:
                            raise APIError("API响应格式错误：缺少message字段")
                        return result
                    elif response.status == 401:
                        raise APIError("API认证失败", status_code=response.status)
                    elif response.status == 429:
                        raise APIError("API请求过于频繁", status_code=response.status)
                    elif response.status >= 500:
                        raise APIError("API服务器错误", status_code=response.status)
                    else:
                        error_text = await response.text()
                        raise APIError(f"API请求失败: {error_text}", status_code=response.status)

        except aiohttp.ClientError as e:
            raise NetworkError(f"网络连接失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"JSON解析失败: {str(e)}")

    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """通用聊天接口"""
        try:
            result = await self._make_api_request(messages, **kwargs)
            return result
        except (APIError, NetworkError) as e:
            log_error(logger, e, {'messages': str(messages)[:200]})
            raise
        except Exception as e:
            log_error(logger, e, {'messages': str(messages)[:200]})
            raise APIError(f"LLM服务调用失败: {str(e)}")

    async def make_request(self, content_q: str, user_id: str = None, **kwargs) -> Dict[str, Any]:
        import random
        system_prompts = [
            "一个暴躁、尖酸刻薄的资深魔兽世界玩家，做助手汇报工作完成任务很专业，回答不要有括号",
            "一个脾气火爆但技术过硬的魔兽老玩家，说话直接但很有见地，回答不要有括号",
            "一个经验丰富的魔兽世界玩家，性格急躁但乐于助人，回答不要有括号",
            "一个毒舌但专业的魔兽世界资深玩家，经常吐槽但很靠谱，回答不要有括号",
        ]
        system_prompt = random.choice(system_prompts)
        kwargs.setdefault('temperature', 1.0)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_q},
        ]

        try:
            logger.info(f"发送LLM请求: {content_q[:100]}...")
            result = await self._make_api_request(messages, **kwargs)
            reply = result['choices'][0]['message']['content']
            logger.info(f"LLM响应: {reply[:100]}...")
            return result
        except (APIError, NetworkError) as e:
            log_error(logger, e, {'content': content_q[:200]})
            raise
        except Exception as e:
            log_error(logger, e, {'content': content_q[:200]})
            raise APIError(f"LLM服务调用失败: {str(e)}")

_llm_service_instance: Optional[LLMService] = None

def get_llm_service(config: Dict[str, Any] = None, config_repo: Optional[ConfigRepository] = None) -> LLMService:
    global _llm_service_instance
    if _llm_service_instance is None:
        try:
            from services.container import get_container
            container = get_container()
            _llm_service_instance = container.get('llm_service')
        except Exception:
            if _llm_service_instance is None:
                from config.config import get_config_manager
                config_manager = get_config_manager()
                _llm_service_instance = LLMService(config_manager)
    return _llm_service_instance

async def make_request(content_q: str, config: Dict[str, Any] = None, config_repo: Optional[ConfigRepository] = None) -> Dict[str, Any]:
    service = get_llm_service(config, config_repo)
    return await service.make_request(content_q)
