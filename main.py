import logging
from telegram import Update

from commands import command_registry, load_plugins, regex_registry
from utils import CustomFileHandler, EnvConfig
from log import logger

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# 加载日志
env = EnvConfig().get_env()

# 日志相关
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[CustomFileHandler("bot.log", mode='w', max_lines=1000), logging.StreamHandler()])

# 提高权限，可以注释查看POST
logging.getLogger("httpx").setLevel(logging.WARNING)


async def message_logger(update: Update, context: CallbackContext) -> None:
    """
        记录每条接收到的消息的详细信息
    :param update:
    :param context:
    :return:
    """
    user = update.effective_user
    if user:
        user_info = f"user {user.id}, username: @{user.username}"
    else:
        user_info = "unknown user"

    message_text = update.message.text if update.message else "No text message"

    logger.info(f"Message from {user_info}: {message_text}")


def main():
    """
    启动函数
    :return:
    """
    # 是否需要代理
    need_proxy = env.get("PROXY") != ''
    # 启动类创建
    application = (ApplicationBuilder()
                   .token(env.get("TOKEN"))
                   .proxy_url(env.get("PROXY") if need_proxy else None)
                   .get_updates_proxy_url(env.get("PROXY") if need_proxy else None)
                   .build())
    # 加载插件
    load_plugins()
    # 添加一个消息处理器，它将处理所有文本消息
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message_logger)
    application.add_handler(text_handler)
    # 加载命令处理器
    for cmd, handler_func in command_registry.items():
        application.add_handler(CommandHandler(cmd, handler_func))
    # 加载正则表达式处理器
    for pattern, handler_func in regex_registry.items():
        application.add_handler(MessageHandler(filters.Regex(pattern), handler_func))

    application.run_polling()


if __name__ == '__main__':
    main()
