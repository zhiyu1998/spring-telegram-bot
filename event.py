from typing import Union

from telegram import Update
from telegram._utils.types import FileInput
from telegram.ext import ContextTypes

from log import logger


class Event:
    """
        事件：
        目前封装 update 和 context 对象到一个单独的 Event 类中，并提供一个更简洁的 API 来发送消息。
    """
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update: Update = update
        self.context: ContextTypes.DEFAULT_TYPE = context
        self.text: str = update.message.text
        self.chat_id = update.effective_chat.id
        self.user_name: str = update.effective_user.name

    async def send_message(self, text: str):
        logger.info(text)
        await self.context.bot.send_message(chat_id=self.chat_id, text=text)

    async def send_image(self, image: Union[FileInput, "PhotoSize"]):
        await self.context.bot.send_photo(chat_id=self.chat_id, photo=image)

    async def send_video(self, video: Union[FileInput, "Video"]):
        await self.context.bot.send_video(chat_id=self.chat_id, video=video)