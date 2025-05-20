from khl import Bot, Message
from utils.logging_utils import get_logger
import json
import os
import openai

logger = get_logger(__name__)

async def upd_msg(msg_id: str, content, target_id=None, channel_type='public', bot=None):
    """更新消息"""
    logger.info(f"更新消息 - msg_id: {msg_id}, content: {content}, target_id: {target_id}")
    
    try:
        if not isinstance(content, str):    
            content = json.dumps(content)
            
        data = {'msg_id': msg_id, 'content': content}
        if target_id is not None:
            data['temp_target_id'] = target_id
            
        if channel_type == 'public':
            result = await bot.client.gate.request('POST', 'message/update', data=data)
        else:
            result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
            
        logger.info(f"消息更新结果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"更新消息时发生错误: {str(e)}")
        raise

async def send_to_channel(channel_id: str, content: str, bot: Bot):
    """发送消息到指定频道"""
    try:
        logger.info(f"发送消息到频道 {channel_id}: {content}")
        result = await bot.client.gate.request('POST', 'message/create', data={
            'channel_id': channel_id,
            'content': content
        })
        logger.info(f"发送消息结果: {result}")
        return result
    except Exception as e:
        logger.error(f"发送消息到频道时发生错误: {str(e)}")
        raise

async def send_direct_message(user_id: str, content: str, bot: Bot):
    """发送私信给指定用户"""
    try:
        logger.info(f"发送私信给用户 {user_id}: {content}")
        result = await bot.client.gate.request('POST', 'direct-message/create', data={
            'target_id': user_id,
            'content': content
        })
        logger.info(f"发送私信结果: {result}")
        return result
    except Exception as e:
        logger.error(f"发送私信时发生错误: {str(e)}")
        raise 


# async def make_gpt_request(prompt: str) -> str:
#     """
#     调用GPT API生成回复
    
#     Args:
#         prompt: 提示文本
        
#     Returns:
#         str: GPT生成的回复
#     """
#     try:
#         # 从环境变量获取API密钥
#         openai.api_key = os.getenv('OPENAI_API_KEY')
        
#         # 调用GPT API
#         response = await openai.ChatCompletion.acreate(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=150,
#             temperature=0.8
#         )
        
#         # 提取回复内容
#         return response.choices[0].message.content.strip()
#     except Exception as e:
#         logger.error(f"GPT API调用失败: {str(e)}")
#         return "抱歉，我现在有点累，待会再说吧~" 
