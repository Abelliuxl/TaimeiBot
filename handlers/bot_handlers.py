from khl import Bot
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def register_bot_handlers(bot: Bot):
    @bot.on_startup
    async def bot_startup(bot_: Bot):
        logger.info("机器人已启动并连接到服务器")
        try:
            me = await bot_.client.gate.request('GET', 'user/me')
            logger.info(f"机器人信息 - 名称: {me.get('username', 'unknown')}, ID: {me.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"获取机器人信息失败: {str(e)}")

    @bot.on_shutdown
    async def bot_shutdown(bot_: Bot):
        logger.info("机器人已关闭连接")
