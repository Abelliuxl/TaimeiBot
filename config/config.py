import json
import os
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def load_config() -> dict:
    """加载配置文件"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error("配置文件不存在")
        raise
    except json.JSONDecodeError:
        logger.error("配置文件格式错误")
        raise

config = load_config()

BOT_TOKEN = config.get("token")
VERIFY_TOKEN = config.get("verify_token")
ENCRYPT_TOKEN = config.get("encrypt_token")
