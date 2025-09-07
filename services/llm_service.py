import requests
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def make_request(content_q: str, config: dict):
    """调用大语言模型API"""
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "一个暴躁、尖酸刻薄的资深魔兽世界玩家，做助手汇报工作完成任务很专业"},
            {"role": "user", "content": content_q},
        ]
    }   

    # 发送API请求
    response = requests.post(
        config['openai_api2d_url'],
        headers={'Authorization': f'Bearer {config["openai_api2d_api_key"]}'},
        json=data,
    )

    # 检查错误
    response.raise_for_status()
    return response.json()

def translate_request(content_q: str, config: dict):
    """翻译功能的API调用"""
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Whenever I send you a message, you need to translate the sentence for me. If the sentence is in Chinese, translate it into English; if it's in English, translate it into Chinese. if it is not English or Chinese, translate it into English and Chinese. The translation must be accurate and natural, without any other extra irrelevant content."},
            {"role": "user", "content": content_q},
        ]
    }   

    # 发送API请求
    response = requests.post(
        config['openai_api2d_url'],
        headers={'Authorization': f'Bearer {config["openai_api2d_api_key"]}'},
        json=data,
    )

    # 检查错误
    response.raise_for_status()
    return response.json()
