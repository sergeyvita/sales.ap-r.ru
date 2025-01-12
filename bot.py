import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils.executor import start_webhook
from aiohttp import web
from bs4 import BeautifulSoup
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Переменные окружения
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 5000))

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
Bot.set_current(bot)  # Устанавливаем текущий экземпляр бота
dp = Dispatcher(bot)

# Обработчик сообщений
@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот Ассоциации застройщиков. Напишите название ЖК, чтобы получить информацию.")

@dp.message_handler()
async def handle_message(message: types.Message):
    query = message.text.strip()
    logger.info(f"Получен запрос на поиск ЖК: '{query}' от пользователя {message.from_user.id}")

    try:
        await message.reply(f"Ищу информацию о ЖК '{query}'...")
        
        # Парсинг главной страницы
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ap-r.ru") as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Парсим список городов
                cities = {}
                select = soup.find("select", id="header_cities")
                if select:
                    for option in select.find_all("option"):
                        if option.get("value") and option["value"] != "/":
                            cities[option.text.strip()] = f"https://ap-r.ru{option['value']}"

                logger.info(f"Итоговый список городов: {cities}")

                # Ищем ЖК в каждом городе
                for city_name, city_url in cities.items():
                    logger.debug(f"Ищу ЖК '{query}' в городе {city_name} ({city_url})")
                    async with session.get(city_url) as city_response:
                        city_html = await city_response.text()
                        city_soup = BeautifulSoup(city_html, "html.parser")

                        # Ищем блок ЖК
                        tile = city_soup.find("a", class_="object-tile-title", string=lambda text: text and query.lower() in text.lower())
                        if tile:
                            full_url = f"https://ap-r.ru{tile['href']}"
                            logger.info(f"Найден ЖК: {query} -> {full_url}")
                            await message.reply(f"Найден ЖК: {query}\n{full_url}")
                            return

        # Если ЖК не найден
        await message.reply(f"ЖК '{query}' не найден. Попробуйте уточнить запрос.")
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.reply("Произошла ошибка при поиске. Попробуйте позже.")

# Настройка вебхука
async def on_startup(app):
    logger.info("Установка вебхука...")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    logger.info("Удаление вебхука...")
    await bot.delete_webhook()

# Маршрут для обработки вебхуков
async def handle_webhook(request):
    update = await request.json()
    logger.info(f"Получен вебхук: {update}")
    update = types.Update.to_object(update)
    await dp.process_update(update)
    return web.Response()

# Настройка приложения Aiohttp
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Запуск приложения
if __name__ == "__main__":
    logger.info("Запуск приложения...")
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True, port=PORT, host="0.0.0.0", web_app=app)
