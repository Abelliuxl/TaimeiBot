import asyncio
import os
from khl import Bot
from handlers.message_handlers import register_message_handlers
from handlers.event_handlers import register_event_handlers
from handlers.bot_handlers import register_bot_handlers
from utils.logging_utils import get_logger
from services.container import initialize_services, get_container
from config.config import initialize_config

logger = get_logger(__name__)

async def initialize_application():
    """初始化应用程序"""
    try:
        # 初始化配置
        config_manager = initialize_config()
        logger.info("配置初始化完成")
        
        # 初始化服务容器
        container = await initialize_services()
        logger.info("服务容器初始化完成")
        
        # 获取配置
        config = config_manager.get_config()
        bot_token = config.get('bot_token')
        
        # 创建机器人实例
        bot = Bot(token=bot_token)
        
        # 将配置和服务容器存储在bot实例中
        bot.config = config
        bot.container = container
        bot.config_manager = config_manager
        
        logger.info("机器人实例创建成功")
        
        # 注册处理器
        register_bot_handlers(bot)
        register_message_handlers(bot)
        register_event_handlers(bot)
        
        logger.info("所有处理器注册完成")
        
        return bot
        
    except Exception as e:
        logger.error(f"应用程序初始化失败: {str(e)}")
        raise

async def async_main():
    """异步主程序入口"""
    bot = None
    try:
        # 初始化应用程序
        bot = await initialize_application()
        
        # 启动机器人
        logger.info("正在启动机器人...")
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"机器人运行时发生错误: {str(e)}")
        raise
    finally:
        # 清理资源
        try:
            if bot:
                container = get_container()
                if container:
                    container.clear()
                    logger.info("资源清理完成")
        except Exception as e:
            logger.warning(f"资源清理时发生错误: {str(e)}")

def main_sync():
    """同步主程序入口（用于兼容性）"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行时发生错误: {str(e)}")
        raise

if __name__ == '__main__':
    main_sync()
