import os
from khl import Bot
from handlers.message_handlers import register_message_handlers
from handlers.event_handlers import register_event_handlers
from handlers.bot_handlers import register_bot_handlers
from utils.logging_utils import get_logger
from config.config import BOT_TOKEN, config

logger = get_logger(__name__)

def main():
    """主程序入口"""
    try:
        # 创建机器人实例
        bot = Bot(token=BOT_TOKEN)
        # 将配置存储在bot实例中，以便handlers可以访问
        bot.config = config
        logger.info("机器人实例创建成功")

        # 注册处理器
        register_bot_handlers(bot)
        register_message_handlers(bot)
        register_event_handlers(bot)
        
        # 启动机器人
        logger.info("正在启动机器人...")
        bot.run()
        
    except Exception as e:
        logger.error(f"机器人运行时发生错误: {str(e)}")
        raise

if __name__ == '__main__':
    main()