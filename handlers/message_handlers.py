from khl import Message, Bot, MessageTypes
import requests
import re
import random
from utils.logging_utils import get_logger
from services import message_service
from services.raider_service import fetch_talent_loadouts
import datetime

logger = get_logger(__name__)
current_time = datetime.datetime.now()

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

async def handle_mention(msg: Message, bot: Bot):
    """处理@消息"""
    try:
        content = msg.content
        logger.info(f"处理@消息: {content}")
        
        # 如果只是@机器人（去掉空格后只剩@标记）
        if content.replace(" ", "") == "(met)726976194(met)":
            logger.info("收到单独@，回复：鸡你太美")
            await msg.ctx.channel.send("鸡你太美")
            return
            
        # 如果@机器人并带有其他内容
        if "(met)726976194(met)" in content:
            new_content = content.replace("(met)726976194(met)", "你")
            logger.info(f"{current_time} - ❓提问： {new_content}")
            try:
                response = make_request(new_content, bot.config)
                reply = response['choices'][0]['message']['content']
                await msg.ctx.channel.send(reply)
                logger.info(f"{current_time} - 🙃回答： {reply}")
            except Exception as e:
                logger.error(f"调用AI API时发生错误: {str(e)}")
                await msg.ctx.channel.send("鸡你太美")
                
    except Exception as e:
        logger.error(f"处理@消息时发生错误: {str(e)}")
        await msg.ctx.channel.send("鸡你太美")

async def handle_text_msg(msg: Message, bot: Bot):
    """处理文本消息"""
    try:
        # 记录消息内容
        logger.info(f"收到消息 - 频道: {msg.ctx.channel.id}, 用户: {msg.author_id}, 内容: {msg.content}")
        
        # 如果是系统消息（@消息），优先处理
        if "(met)726976194(met)" in msg.content:
            await handle_mention(msg, bot)
            return
            
        # 在特定频道进行翻译
        if msg.target_id in ["9446829885813673", "4113108449843636"]:
            content_mention = re.sub(r'\(met\).*?\(met\)', '', msg.content).strip()
            logger.info(f"{current_time} - ❓提问： {content_mention}")
            
            try:
                # 调用翻译API
                content = translate_request(content_mention, bot.config)
                
                # 发送翻译结果
                await msg.reply(content['choices'][0]['message']['content'])
                logger.info(f"{current_time} - 🙃回答： {content['choices'][0]['message']['content']}")
                return
                
            except Exception as e:
                logger.info(f"{current_time} - 发生异常：{e}")
                await msg.reply("鸡你太美")
                return
            
        # 检查是否是 /tf 命令
        tf_match = re.match(r'(?is)/tf(.+)', msg.content)
        if tf_match:
            content = tf_match.group(1).strip()
            logger.info(f"处理/tf命令，查询内容: {content}")
            
            if not content or content.isspace():
                await msg.reply("缺少具体职业，输入职业简称/tf 惩戒骑")
                return
                
            result = await fetch_talent_loadouts(content)
            if result is None:
                await msg.reply("无法找到匹配的职业和专精")
                return
                
            await msg.reply(result)
            return
            
        # 检查是否是 /tm 命令
        tm_match = re.match(r'(?s)/[tT][mM](.+)', msg.content)
        if tm_match:
            content_q = tm_match.group(1).strip()
            logger.info(f"处理/tm命令，问题内容: {content_q}")
            try:
                response = make_request(content_q, bot.config)
                await msg.ctx.channel.send(response['choices'][0]['message']['content'])
                logger.info(f"AI回复: {response['choices'][0]['message']['content']}")
                return
            except Exception as e:
                logger.error(f"调用AI API时发生错误: {str(e)}")
                await msg.ctx.channel.send("鸡你太美")
                return
        
        # 检查是否是发送消息命令
        send_match = re.match(r'/send\s+(\S+)\s+(.+)', msg.content)
        if send_match:
            channel_id = send_match.group(1)
            content = send_match.group(2)
            try:
                await message_service.send_to_channel(channel_id, content, bot)
                await msg.ctx.channel.send(f"消息已发送到频道 {channel_id}")
                return
            except Exception as e:
                logger.error(f"发送消息时发生错误: {str(e)}")
                await msg.ctx.channel.send("发送消息失败")
                return
                
        # 检查是否是发送私信命令
        dm_match = re.match(r'/dm\s+(\S+)\s+(.+)', msg.content)
        if dm_match:
            user_id = dm_match.group(1)
            content = dm_match.group(2)
            try:
                await message_service.send_direct_message(user_id, content, bot)
                await msg.ctx.channel.send(f"私信已发送给用户 {user_id}")
                return
            except Exception as e:
                logger.error(f"发送私信时发生错误: {str(e)}")
                await msg.ctx.channel.send("发送私信失败")
                return
        
        # 如果是其他命令，交给命令处理器处理
        if msg.content.startswith('/'):
            await handle_command(msg, bot)
            return
            
        # 处理普通消息，有10%的概率随机回复
        keywords = ['tf', 'moni', 'gf', 'cs', 'tm', 'mnsx']
        pattern = re.compile('|'.join(keywords), re.IGNORECASE)
        
        if random.randint(1, 100) > 90 and not pattern.search(msg.content):
            content = msg.content
            logger.info(f"{current_time} - ❓提问： {content}")
            content_extend = """你是一个暴躁易怒，尖酸刻薄的人，偶尔看到了群里有人发了这个消息，你觉得非常烦，于是很刻薄地回复他/她，但是不要超过50个字，他的消息是：""" + content
            try:
                response = make_request(content_extend, bot.config)
                comments = response['choices'][0]['message']['content']
                logger.info(f"{current_time} - 🙃回答： {comments}")
                await msg.ctx.channel.send('(met)' + msg.author_id + '(met)' + comments)
            except Exception as e:
                logger.error(f"随机回复时发生错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"处理文本消息时发生错误: {str(e)}")
        await msg.ctx.channel.send("抱歉，处理消息时出现了错误。")

async def handle_command(msg: Message, bot: Bot):
    """处理命令消息"""
    try:
        command = msg.content.split()[0][1:]  # 去掉开头的/
        logger.info(f"收到命令: {command}")
        
        if command == "help":
            help_text = """可用命令:
/help - 显示帮助信息
/ping - 测试机器人是否在线
/tm <内容> - 与AI对话
/send <频道ID> <内容> - 发送消息到指定频道
/dm <用户ID> <内容> - 发送私信给指定用户"""
            await msg.ctx.channel.send(help_text)
        elif command == "ping":
            await msg.ctx.channel.send("pong!")
        else:
            await msg.ctx.channel.send(f"未知命令: {command}\n使用 /help 查看可用命令")
            
    except Exception as e:
        logger.error(f"处理命令时发生错误: {str(e)}")
        await msg.ctx.channel.send("抱歉，处理命令时出现了错误。") 