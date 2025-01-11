import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.dispatcher.webhook import SendMessage
import asyncio
import os

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Настройка токена и хостинга
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "your-telegram-bot-token")
WEBHOOK_HOST = "https://your-render-webhook-url.com"
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    try:
        await message.reply("Привет! Я бот для поиска информации по жилым комплексам.")
    except TelegramAPIError as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await message.reply("Произошла ошибка при обработке команды. Попробуйте снова.")

@dp.message_handler()
async def handle_message(message: types.Message):
    try:
        # Заглушка для поиска ЖК
        if "ЖК" in message.text:
            await message.reply(f"Ищу информацию о {message.text}, пожалуйста, подождите...")
            # Логика поиска информации
            await asyncio.sleep(2)  # Имитируем время обработки
            await message.reply(f"Информация о {message.text} найдена.")
        else:
            await message.reply("Введите название ЖК для поиска.")
    except TelegramAPIError as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await message.reply("Произошла ошибка при обработке вашего запроса. Попробуйте снова.")

async def on_startup(dp):
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook установлен: {WEBHOOK_URL}")
    except TelegramAPIError as e:
        logger.error(f"Ошибка установки Webhook: {e}")
        raise

async def on_shutdown(dp):
    try:
        await bot.delete_webhook()
        logger.info("Webhook удалён.")
    except TelegramAPIError as e:
        logger.error(f"Ошибка удаления Webhook: {e}")

if __name__ == "__main__":
    try:
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host="0.0.0.0",
            port=8443,
        )
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
