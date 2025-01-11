import os
import json
from khl import Bot, Message, EventTypes
from handlers import message_handlers, event_handlers
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def load_config() -> dict:
    """加载配置文件"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error("配置文件不存在")
        raise
    except json.JSONDecodeError:
        logger.error("配置文件格式错误")
        raise

def main():
    """主程序入口"""
    try:
        # 加载配置
        config = load_config()
        logger.info("配置加载成功")
        
        # 创建机器人实例
        bot = Bot(token=config['token'])
        # 将配置存储在bot实例中，以便handlers可以访问
        bot.config = config
        logger.info("机器人实例创建成功")

        # 添加连接状态回调
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
        
        # 注册消息处理器
        @bot.on_message()
        async def message_handler(msg: Message):
            try:
                logger.info(f"收到消息: {msg.content}")
                await message_handlers.handle_text_msg(msg, bot)
            except Exception as e:
                logger.error(f"处理消息时发生错误: {str(e)}")
        
        # 注册事件处理器
        @bot.on_event(EventTypes.JOINED_CHANNEL)
        async def join_handler(bot_: Bot, event):
            try:
                logger.info("收到加入语音频道事件")
                await event_handlers.handle_join_channel(event, bot)
            except Exception as e:
                logger.error(f"处理加入语音频道事件时发生错误: {str(e)}")
        
        @bot.on_event(EventTypes.EXITED_CHANNEL)
        async def leave_handler(bot_: Bot, event):
            try:
                logger.info("收到退出语音频道事件")
                await event_handlers.handle_leave_channel(event, bot)
            except Exception as e:
                logger.error(f"处理退出语音频道事件时发生错误: {str(e)}")
        
        # 启动机器人
        logger.info("正在启动机器人...")
        bot.run()
        
    except Exception as e:
        logger.error(f"机器人运行时发生错误: {str(e)}")
        raise

if __name__ == '__main__':
    main() 