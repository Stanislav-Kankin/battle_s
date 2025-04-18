from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
# ADMINS = [123456789]  # ID админов (если нужны)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Новый формат
)
