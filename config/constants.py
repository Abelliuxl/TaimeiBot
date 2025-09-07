"""
TaimeiBot 常量配置文件
集中管理所有硬编码的常量值
"""

from typing import List, Dict, Any

# 机器人配置
DEFAULT_BOT_ID: str = "726976194"
DEFAULT_WEBHOOK_PORT: int = 50000
DEFAULT_USING_WS: bool = True

# 频道配置
DEFAULT_TRANSLATION_CHANNELS: List[str] = ["9446829885813673", "4113108449843636"]
DEFAULT_ADMIN_CHANNELS: List[str] = []

# API配置
DEFAULT_LLM_API_URL: str = "https://api.openai.com/v1/chat/completions"

# 功能开关配置
DEFAULT_ENABLE_TRANSLATION: bool = True
DEFAULT_ENABLE_TALENT_QUERY: bool = True
DEFAULT_ENABLE_AI_CHAT: bool = True
DEFAULT_ENABLE_RANDOM_REPLY: bool = True

# 消息配置
DEFAULT_ERROR_MESSAGE: str = "鸡你太美"
DEFAULT_TIMEOUT_MESSAGE: str = "请求超时，请稍后再试"
DEFAULT_RATE_LIMIT_MESSAGE: str = "请求过于频繁，请稍后再试"

# 缓存配置
DEFAULT_CACHE_TTL: int = 3600  # 1小时
DEFAULT_RAIDER_CACHE_TTL: int = 1800  # 30分钟
DEFAULT_TRANSLATION_CACHE_TTL: int = 86400  # 24小时

# 重试配置
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_DELAY: float = 1.0

# 限流配置
DEFAULT_RATE_LIMIT_REQUESTS: int = 100
DEFAULT_RATE_LIMIT_WINDOW: int = 60  # 60秒

# 日志配置
DEFAULT_LOG_LEVEL: str = "INFO"
DEFAULT_LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_FILE: str = "logs/taimeibot.log"

# 命令配置
COMMAND_PREFIX: str = "/"
COMMAND_TALENT: str = "tf"  # 根据用户实际使用情况修改
COMMAND_TRANSLATE: str = "tr"
COMMAND_AI: str = "ai"
COMMAND_HELP: str = "help"

# 正则表达式模式
RAIDER_IO_URL_PATTERN: str = r"https?://(www\.)?raider\.io"
TALENT_QUERY_PATTERN: str = r"/tf\s+([^/]+)(?:/([^/]+))?(?:/([^/]+))?"
TRANSLATION_PATTERN: str = r"/tr\s+([^/]+)(?:/([^/]+))?"
AI_CHAT_PATTERN: str = r"/ai\s+(.+)"

# 支持的游戏区域
SUPPORTED_REGIONS: List[str] = ["cn", "us", "eu", "kr", "tw"]

# 支持的游戏职业
SUPPORTED_CLASSES: Dict[str, List[str]] = {
    "warrior": ["arms", "fury", "protection"],
    "paladin": ["holy", "protection", "retribution"],
    "hunter": ["beast_mastery", "marksmanship", "survival"],
    "rogue": ["assassination", "outlaw", "subtlety"],
    "priest": ["discipline", "holy", "shadow"],
    "death_knight": ["blood", "frost", "unholy"],
    "shaman": ["elemental", "enhancement", "restoration"],
    "mage": ["arcane", "fire", "frost"],
    "warlock": ["affliction", "demonology", "destruction"],
    "monk": ["brewmaster", "windwalker", "mistweaver"],
    "druid": ["balance", "feral", "guardian", "restoration"],
    "demon_hunter": ["havoc", "vengeance"],
    "evoker": ["devastation", "preservation"]
}

# 默认天赋配置
DEFAULT_TALENT_CONFIG: Dict[str, Any] = {
    "default_region": "cn",
    "default_class": "warrior",
    "default_spec": "arms",
    "max_level": 70
}

# 翻译配置
TRANSLATION_CONFIG: Dict[str, Any] = {
    "max_text_length": 5000,
    "supported_languages": ["en", "zh", "ja", "ko"],
    "default_source_lang": "auto",
    "default_target_lang": "zh"
}

# AI聊天配置
AI_CHAT_CONFIG: Dict[str, Any] = {
    "max_context_length": 4000,
    "max_response_length": 1000,
    "temperature": 0.8,  # 基础温度
    "temperature_range": [0.6, 1.0],  # 温度范围，用于随机化（最大值为1.0）
    "system_prompt": "你是一个友好的AI助手，请简洁地回答用户的问题。"
}

# 帮助信息
HELP_MESSAGES: Dict[str, str] = {
    "talent": "查询天赋：/tf [职业专精简称]\n示例：/tf ms 或 /tf 恶魔学识",
    "translate": "翻译文本：/tr [文本]\n示例：/tr Hello World 或 /tr 你好世界",
    "ai": "AI聊天：/ai [问题]\n示例：/ai 今天天气怎么样？",
    "help": "显示帮助信息：/help"
}

# 错误代码
ERROR_CODES: Dict[str, str] = {
    "CONFIG_ERROR": "配置错误",
    "API_ERROR": "API调用错误",
    "NETWORK_ERROR": "网络错误",
    "VALIDATION_ERROR": "验证错误",
    "RATE_LIMIT_ERROR": "限流错误",
    "TIMEOUT_ERROR": "超时错误",
    "UNKNOWN_ERROR": "未知错误"
}

# 版本信息
VERSION: str = "1.2.0"
BUILD_DATE: str = "2025-01-07"
AUTHOR: str = "TaimeiBot Team"
DESCRIPTION: str = "一个功能丰富的Discord机器人，提供天赋查询、翻译、AI聊天等功能"
