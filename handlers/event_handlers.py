from khl import Bot, Event, EventTypes
from utils.logging_utils import get_logger
from handlers.message_handlers import make_request
from utils.voice_utils import join_voice_channel, stream_audio_to_voice, leave_voice_channel
from config.config import BOT_TOKEN
from utils.voice_utils import get_audio_for_user


logger = get_logger(__name__)

# 配置发送消息的频道列表
NOTIFICATION_CHANNEL_IDS = ["8099606056795106", "4932665341111852"]

async def handle_join_channel(event: Event, bot: Bot):
    """处理用户加入频道事件"""
    logger.info("Event triggered: JOINED_CHANNEL")
    
    channel = await bot.client.fetch_public_channel(event.body['channel_id'])
    user_id = event.body['user_id']
    audio_path = get_audio_for_user(user_id)

    channel_id = event.body['channel_id']  # ✅ 添加这行
    
    logger.info(f"Channel fetched: {channel} channel_id: {event.body['channel_id']}")
    logger.info(f"User ID: {user_id}")
    
    if audio_path:
        try:
            voice_data = await join_voice_channel(channel_id, BOT_TOKEN)
            logger.info(f"🎯 KOOK voice_data: {voice_data}")
            await stream_audio_to_voice(voice_data, audio_path)
            logger.info(f"为用户 {user_id} 推送了语音：{audio_path}")
            await leave_voice_channel(channel_id, BOT_TOKEN)
            logger.info("已自动离开语音频道")
        except Exception as e:
            logger.error(f"语音推流失败: {e}")
    else:
        logger.info(f"用户 {user_id} 不在 MONITORED_MEMBERS 中，跳过推流")

    guild = await bot.client.fetch_guild(channel.guild_id)
    guild_channel_list = await guild.fetch_channel_list()

    if user_id == "726976194":
        logger.info("目标用户 726976194 加入语音频道，跳过发送公屏消息。")
        return
    
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

    if user_id == "726976194":
        logger.info("目标用户 726976194 离开语音频道，跳过发送公屏消息。")
        return

    
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