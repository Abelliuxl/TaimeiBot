from khl import Bot, Event, EventTypes
from utils.logging_utils import get_logger
from handlers.message_handlers import make_request

logger = get_logger(__name__)

# 配置发送消息的频道列表
NOTIFICATION_CHANNEL_IDS = ["8099606056795106", "4932665341111852"]

async def handle_join_channel(event: Event, bot: Bot):
    """处理用户加入频道事件"""
    logger.info("Event triggered: JOINED_CHANNEL")
    
    channel = await bot.client.fetch_public_channel(event.body['channel_id'])
    user_id = event.body['user_id']
    
    logger.info(f"Channel fetched: {channel} channel_id: {event.body['channel_id']}")
    logger.info(f"User ID: {user_id}")
    
    guild = await bot.client.fetch_guild(channel.guild_id)
    guild_channel_list = await guild.fetch_channel_list()
    
    for guild_channel in guild_channel_list:
        if guild_channel.id in NOTIFICATION_CHANNEL_IDS:
            content = "你是一个心胸狭窄的憨憨，人菜脾气大，有个比你厉害比你优秀比你帅的来游戏语音频道了，你很不服气，准备了一番话对他阴阳怪气（不超过150字），你说道："
            
            try:
                response = make_request(content, bot.config)
                gpt_response = response['choices'][0]['message']['content']
                respond_channel = await bot.client.fetch_public_channel(guild_channel.id)
                await bot.client.send(respond_channel, f'(met){user_id}(met){gpt_response}')
                logger.info(f"Message sent to channel {guild_channel.id}")
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")

async def handle_leave_channel(event: Event, bot: Bot):
    """处理用户退出频道事件"""
    logger.info("Event triggered: EXITED_CHANNEL")
    
    channel = await bot.client.fetch_public_channel(event.body['channel_id'])
    user_id = event.body['user_id']
    user = await bot.client.fetch_user(user_id)
    user_name = user.username
    
    logger.info(f"User name: {user_name}")
    logger.info(f"User ID: {user_id}")
    
    guild = await bot.client.fetch_guild(channel.guild_id)
    guild_channel_list = await guild.fetch_channel_list()
    
    for guild_channel in guild_channel_list:
        if guild_channel.id in NOTIFICATION_CHANNEL_IDS:
            content = f"你是一个心胸狭窄的憨憨，人菜脾气大，有个比你厉害比你优秀比你帅的人，叫{user_name},打完游戏离开游戏语音频道了，你看他走了你来劲了，准备了一番话在公屏上阴阳怪气,并调侃他的名字（不超过150字），你说道："
            
            try:
                response = make_request(content, bot.config)
                gpt_response = response['choices'][0]['message']['content']
                respond_channel = await bot.client.fetch_public_channel(guild_channel.id)
                await bot.client.send(respond_channel, f'\n\n{gpt_response}')
                logger.info(f"Message sent to channel {guild_channel.id}")
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}") 