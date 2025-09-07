from khl import Message, Bot, MessageTypes
import re
import random
import datetime
from typing import Optional
from utils.logging_utils import get_logger
from utils.base_errors import TaimeiBotError
from utils.error_handler import APIError, NetworkError, ValidationError, RateLimitError, log_error
from services import message_service
from services.llm_service import make_request
from handlers.commands import (
    BaseCommand, CommandRegistry, TalentCommand, 
    HelpCommand  # AIChatCommand and TranslationCommand removed
)
from services.data import ConfigRepository
from utils.input_validator import (
    validate_command, validate_talent_query, validate_translation, 
    validate_ai_chat, validate_user_input
)
from utils.rate_limiter import (
    check_command_rate_limit, check_talent_rate_limit, 
    check_translation_rate_limit, check_ai_chat_rate_limit
)
import os

logger = get_logger(__name__)

class MessageHandler:
    """消息处理器主类"""
    
    def __init__(self):
        self.command_registry = CommandRegistry()
        self.config_repo: Optional[ConfigRepository] = None
        self._setup_commands()
    
    def _setup_commands(self):
        """设置命令系统"""
        # 创建命令实例
        talent_cmd = TalentCommand()
        # translation_cmd = TranslationCommand() # Removed
        # ai_chat_cmd = AIChatCommand() # Removed
        help_cmd = HelpCommand()
        
        # 注册命令
        self.command_registry.register(talent_cmd)
        # self.command_registry.register(translation_cmd) # Removed
        # self.command_registry.register(ai_chat_cmd) # Removed
        self.command_registry.register(help_cmd)
        
        # 设置帮助命令的命令注册表引用
        help_cmd.set_command_registry(self.command_registry)
    
    def initialize(self, bot: Bot, config: dict):
        """初始化消息处理器"""
        # 初始化配置仓库
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(current_dir)  # 获取项目根目录
        self.config_repo = ConfigRepository(base_dir)
        
        # 为所有命令设置上下文
        self.command_registry.set_context(bot, config)
        
        logger.info("消息处理器初始化完成")
    
    async def handle_text_message(self, msg: Message, bot: Bot):
        """处理文本消息"""
        try:
            # 记录消息内容
            logger.info(f"收到消息 - 频道: {msg.ctx.channel.id}, 用户: {msg.author_id}, 内容: {msg.content}")
            
            # 基础输入验证
            is_valid, error_msg = await validate_user_input(msg.content)
            if not is_valid:
                logger.warning(f"输入验证失败: {error_msg}")
                await self._send_validation_error_reply(msg, error_msg)
                return
            
            # 通用限流检查
            rate_info = await check_command_rate_limit(str(msg.author_id))
            if rate_info.is_limited:
                logger.warning(f"用户 {msg.author_id} 触发限流")
                await self._send_rate_limit_error_reply(msg, rate_info.retry_after)
                return
            
            # 如果是系统消息（@消息），优先处理
            if await self._is_mention_message(msg):
                await self._handle_mention_message(msg, bot)
                return
            
            # 检查是否是命令消息
            if await self._is_command_message(msg):
                await self._handle_command_message(msg, bot)
                return
            
            # 检查是否在翻译频道
            if await self._is_translation_channel(msg):
                await self._handle_translation_message(msg, bot)
                return
            
            # 处理普通消息（随机回复）
            await self._handle_random_reply(msg, bot)
            
        except ValidationError as e:
            logger.warning(f"验证错误: {str(e)}")
            await self._send_validation_error_reply(msg, str(e))
        except RateLimitError as e:
            logger.warning(f"限流错误: {str(e)}")
            await self._send_rate_limit_error_reply(msg)
        except Exception as e:
            log_error(logger, e, {'function': 'handle_text_message', 'user_id': msg.author_id})
            await self._send_error_reply(msg, "抱歉，处理消息时出现了错误。")
    
    async def _is_mention_message(self, msg: Message) -> bool:
        """检查是否是@消息"""
        bot_id = self.config_repo.get_config().get('bot_id', '726976194')
        return f"(met){bot_id}(met)" in msg.content
    
    async def _handle_mention_message(self, msg: Message, bot: Bot):
        """处理@消息"""
        try:
            content = msg.content
            bot_id = self.config_repo.get_config().get('bot_id', '726976194')
            
            # 如果只是@机器人（去掉空格后只剩@标记）
            if content.replace(" ", "") == f"(met){bot_id}(met)":
                logger.info("收到单独@，回复帮助信息")
                help_cmd = self.command_registry.get_command("help")
                if help_cmd:
                    await help_cmd.send_welcome_message(msg)
                return
            
            # 如果@机器人并带有其他内容，当作AI聊天处理
            new_content = content.replace(f"(met){bot_id}(met)", "").strip()
            if new_content:
                logger.info(f"收到@提问: {new_content}")
                await self._handle_ai_chat(msg, new_content, bot)
                
        except Exception as e:
            log_error(logger, e, {'function': '_handle_mention_message'})
            await self._send_error_reply(msg, "抱歉，处理@消息时出现了错误。")
    
    async def _is_command_message(self, msg: Message) -> bool:
        """检查是否是命令消息"""
        return msg.content.startswith('/')
    
    async def _handle_command_message(self, msg: Message, bot: Bot):
        """处理命令消息"""
        try:
            # 解析命令
            command_text = msg.content[1:].strip()  # 去掉开头的/
            if not command_text:
                return
            
            # 命令验证（传递完整的命令文本，包含/前缀）
            is_valid, error_msg = await validate_command(msg.content)
            if not is_valid:
                logger.warning(f"命令验证失败: {error_msg}")
                await self._send_validation_error_reply(msg, error_msg)
                return
            
            # 分割命令和参数
            parts = command_text.split(maxsplit=1)
            command_name = parts[0]
            args = parts[1].split() if len(parts) > 1 else []
            
            logger.info(f"处理命令: {command_name}, 参数: {args}")
            
            # 尝试执行命令
            result = await self.command_registry.execute_command(command_name, msg, args)
            
            # 如果命令未找到 (execute_command returns None), 尝试处理特殊命令
            # 如果命令已找到并处理 (execute_command returns True or a string), 则不执行特殊命令逻辑
            if result is None:
                await self._handle_special_command(msg, command_name, args, bot)
                
        except ValidationError as e:
            logger.warning(f"命令验证错误: {str(e)}")
            await self._send_validation_error_reply(msg, str(e))
        except RateLimitError as e:
            logger.warning(f"命令限流错误: {str(e)}")
            await self._send_rate_limit_error_reply(msg)
        except Exception as e:
            log_error(logger, e, {'function': '_handle_command_message'})
            await self._send_error_reply(msg, "抱歉，处理命令时出现了错误。")
    
    async def _handle_special_command(self, msg: Message, command_name: str, args: list, bot: Bot):
        """处理特殊命令（不在命令系统中的命令）"""
        try:
            if command_name == "ping":
                await msg.reply("pong!")
                logger.info("响应ping命令")
            
            elif command_name == "send" and len(args) >= 2:
                # 发送消息到指定频道
                channel_id = args[0]
                content = " ".join(args[1:])
                await message_service.send_to_channel(channel_id, content, bot)
                await msg.reply(f"消息已发送到频道 {channel_id}")
                logger.info(f"发送消息到频道 {channel_id}")
            
            elif command_name == "dm" and len(args) >= 2:
                # 发送私信给指定用户
                user_id = args[0]
                content = " ".join(args[1:])
                await message_service.send_direct_message(user_id, content, bot)
                await msg.reply(f"私信已发送给用户 {user_id}")
                logger.info(f"发送私信给用户 {user_id}")
            
            else:
                await msg.reply(f"未知命令: {command_name}\n使用 `/help` 查看可用命令")
                logger.warning(f"未知命令: {command_name}")
                
        except Exception as e:
            log_error(logger, e, {'function': '_handle_special_command', 'command': command_name})
            await self._send_error_reply(msg, "抱歉，处理特殊命令时出现了错误。")
    
    async def _is_translation_channel(self, msg: Message) -> bool:
        """检查是否在翻译频道"""
        channel_config = self.config_repo.get_channel_config()
        translation_channels = channel_config.get('translation_channels', [])
        return str(msg.ctx.channel.id) in translation_channels
    
    async def _handle_translation_message(self, msg: Message, bot: Bot):
        """处理翻译消息"""
        try:
            # 移除@标记
            content_mention = re.sub(r'\(met\).*?\(met\)', '', msg.content).strip()
            logger.info(f"收到翻译请求: {content_mention}")
            
            if not content_mention:
                return
            
            # 翻译验证 (validate_translation expects a list of args, so we pass it as a list)
            is_valid, error_msg = await validate_translation([content_mention])
            if not is_valid:
                logger.warning(f"翻译验证失败: {error_msg}")
                await self._send_validation_error_reply(msg, error_msg)
                return
            
            # 翻译限流检查
            rate_info = await check_translation_rate_limit(str(msg.author_id))
            if rate_info.is_limited:
                logger.warning(f"用户 {msg.author_id} 翻译触发限流")
                await self._send_rate_limit_error_reply(msg, rate_info.retry_after)
                return

            # 检查功能开关 (assuming config is loaded in self.config_repo)
            feature_config = self.config_repo.get_feature_config()
            if not feature_config.get('enable_translation', True):
                await self._send_error_reply(msg, "翻译功能当前已禁用")
                return

            logger.info(f"用户 {msg.author_id} 请求翻译: {content_mention}")
            
            # 调用翻译服务
            # Note: make_request is for general LLM, translate_request is specific for translation.
            # We need to import translate_request from services.llm_service
            from services.llm_service import translate_request
            
            result = await translate_request(content_mention, config_repo=self.config_repo)
            
            if result and 'choices' in result and result['choices']:
                translated_text = result['choices'][0]['message']['content'].strip()
                # 发送翻译结果
                await msg.reply(f"📖 翻译结果:\n{translated_text}")
            else:
                await self._send_error_reply(msg, "翻译服务返回结果异常")
                
        except ValidationError as e: # Should be caught by validate_translation, but as a safeguard
            logger.warning(f"翻译验证错误: {str(e)}")
            await self._send_validation_error_reply(msg, str(e))
        except RateLimitError as e: # Should be caught by check_translation_rate_limit, but as a safeguard
            logger.warning(f"翻译限流错误: {str(e)}")
            await self._send_rate_limit_error_reply(msg)
        except Exception as e:
            log_error(logger, e, {'function': '_handle_translation_message'})
            await self._send_error_reply(msg, "抱歉，翻译时出现了错误。")
    
    async def _handle_ai_chat(self, msg: Message, content: str, bot: Bot):
        """处理AI聊天"""
        try:
            # AI聊天验证
            is_valid, error_msg = await validate_ai_chat(content)
            if not is_valid:
                logger.warning(f"AI聊天验证失败: {error_msg}")
                await self._send_validation_error_reply(msg, error_msg)
                return
            
            # AI聊天限流检查
            rate_info = await check_ai_chat_rate_limit(str(msg.author_id))
            if rate_info.is_limited:
                logger.warning(f"用户 {msg.author_id} AI聊天触发限流")
                await self._send_rate_limit_error_reply(msg, rate_info.retry_after)
                return
            
            # 检查功能开关 (assuming config is loaded in self.config_repo)
            feature_config = self.config_repo.get_feature_config()
            if not feature_config.get('enable_ai_chat', True):
                await self._send_error_reply(msg, "AI聊天功能当前已禁用")
                return

            logger.info(f"用户 {msg.author_id} AI聊天: {content}")
            
            # 调用AI聊天服务
            result = await make_request(content, config_repo=self.config_repo)
            
            if result and 'choices' in result and result['choices']:
                ai_reply = result['choices'][0]['message']['content'].strip()
                # 发送AI回复
                await msg.reply(f"🤖 AI助手:\n{ai_reply}")
            else:
                await self._send_error_reply(msg, "AI服务返回结果异常")
                
        except ValidationError as e: # Should be caught by validate_ai_chat, but as a safeguard
            logger.warning(f"AI聊天验证错误: {str(e)}")
            await self._send_validation_error_reply(msg, str(e))
        except RateLimitError as e: # Should be caught by check_ai_chat_rate_limit, but as a safeguard
            logger.warning(f"AI聊天限流错误: {str(e)}")
            await self._send_rate_limit_error_reply(msg)
        except Exception as e:
            log_error(logger, e, {'function': '_handle_ai_chat'})
            await self._send_error_reply(msg, "抱歉，AI聊天时出现了错误。")
    
    async def _handle_random_reply(self, msg: Message, bot: Bot):
        """处理随机回复"""
        try:
            # 检查功能开关
            feature_config = self.config_repo.get_feature_config()
            if not feature_config.get('enable_random_reply', True):
                return
            
            # 有10%的概率随机回复
            if random.randint(1, 100) > 90:
                # 避免回复包含关键词的消息
                keywords = ['tf', 'moni', 'gf', 'cs', 'tm', 'mnsx', '/', 'help', 'ping']
                pattern = re.compile('|'.join(keywords), re.IGNORECASE)
                
                if not pattern.search(msg.content):
                    content = msg.content
                    logger.info(f"随机回复触发，消息内容: {content}")
                    
                    # 构建暴躁回复的提示
                    prompt = """你是一个暴躁易怒，尖酸刻薄的人，偶尔看到了群里有人发了这个消息，你觉得非常烦，于是很刻薄地回复他/她，但是不要超过50个字，他的消息是：""" + content
                    
                    try:
                        response = await make_request(prompt, config_repo=self.config_repo)
                        if response and 'choices' in response and response['choices']:
                            comments = response['choices'][0]['message']['content'].strip()
                            logger.info(f"随机回复: {comments}")
                            await msg.ctx.channel.send(f'(met){msg.author_id}(met){comments}')
                    except Exception as e:
                        log_error(logger, e, {'function': '_handle_random_reply'})
                        # 随机回复失败时不发送错误消息，保持用户体验
        
        except Exception as e:
            log_error(logger, e, {'function': '_handle_random_reply'})
            # 随机回复失败时不发送错误消息，保持用户体验
    
    async def _send_error_reply(self, msg: Message, error_message: str):
        """发送错误回复"""
        try:
            await msg.reply(f"❌ {error_message}")
        except Exception as e:
            logger.error(f"发送错误回复失败: {str(e)}")
    
    async def _send_validation_error_reply(self, msg: Message, error_message: str):
        """发送验证错误回复"""
        try:
            await msg.reply(f"⚠️ 输入验证失败: {error_message}")
        except Exception as e:
            logger.error(f"发送验证错误回复失败: {str(e)}")
    
    async def _send_rate_limit_error_reply(self, msg: Message, retry_after: Optional[float] = None):
        """发送限流错误回复"""
        try:
            if retry_after:
                await msg.reply(f"🚫 请求过于频繁，请 {retry_after:.1f} 秒后重试")
            else:
                await msg.reply(f"🚫 请求过于频繁，请稍后重试")
        except Exception as e:
            logger.error(f"发送限流错误回复失败: {str(e)}")

# 全局消息处理器实例
_message_handler: Optional[MessageHandler] = None

def get_message_handler() -> MessageHandler:
    """获取消息处理器实例"""
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler()
    return _message_handler

def register_message_handlers(bot: Bot):
    """注册消息处理器"""
    message_handler = get_message_handler()
    
    @bot.on_message()
    async def message_handler_func(msg: Message):
        try:
            # 确保消息处理器已初始化
            if not message_handler.config_repo:
                message_handler.initialize(bot, bot.config)
            
            logger.debug(f"收到消息: {msg.content}")
            await message_handler.handle_text_message(msg, bot)
        except Exception as e:
            log_error(logger, e, {'function': 'message_handler_func'})
            try:
                await msg.ctx.channel.send("抱歉，处理消息时出现了严重错误。")
            except:
                logger.error("无法发送错误回复消息")

# 为了向后兼容，保留原有的函数接口
async def handle_mention(msg: Message, bot: Bot):
    """处理@消息（向后兼容函数）"""
    message_handler = get_message_handler()
    if not message_handler.config_repo:
        message_handler.initialize(bot, bot.config)
    await message_handler._handle_mention_message(msg, bot)

async def handle_text_msg(msg: Message, bot: Bot):
    """处理文本消息（向后兼容函数）"""
    message_handler = get_message_handler()
    if not message_handler.config_repo:
        message_handler.initialize(bot, bot.config)
    await message_handler.handle_text_message(msg, bot)

async def handle_command(msg: Message, bot: Bot):
    """处理命令消息（向后兼容函数）"""
    message_handler = get_message_handler()
    if not message_handler.config_repo:
        message_handler.initialize(bot, bot.config)
    await message_handler._handle_command_message(msg, bot)
