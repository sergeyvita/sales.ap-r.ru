import os
import logging
import requests
from aiohttp import web
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# Настройки
BASE_URL = "https://ap-r.ru"

# Инициализация переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 5000))

# Инициализация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Инициализация Aiohttp приложения
app = web.Application()

# Функция парсинга городов с главной страницы
def get_city_links():
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        city_links = {}
        for link in soup.select("a.city-link"):
            city_name = link.text.strip()
            city_url = BASE_URL + link["href"]
            city_links[city_name] = city_url
        return city_links
    except Exception as e:
        logger.error(f"Ошибка парсинга городов: {e}")
        return {}

# Функция парсинга ЖК в городе
def get_housing_complex_links(city_url):
    try:
        response = requests.get(city_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        housing_complexes = {}
        for link in soup.select("a.complex-link"):
            complex_name = link.text.strip()
            complex_url = BASE_URL + link["href"]
            housing_complexes[complex_name] = complex_url
        return housing_complexes
    except Exception as e:
        logger.error(f"Ошибка парсинга ЖК: {e}")
        return {}

# Хендлер для команды /start
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Добро пожаловать! Напишите название города или ЖК, чтобы получить информацию.")

# Хендлер для обработки текстовых сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    query = message.text.strip()
    await message.reply("Ищу информацию...")

    city_links = get_city_links()
    if not city_links:
        await message.reply("Не удалось получить список городов. Попробуйте позже.")
        return

    for city_name, city_url in city_links.items():
        if query.lower() in city_name.lower():
            housing_complexes = get_housing_complex_links(city_url)
            if not housing_complexes:
                await message.reply(f"Не удалось найти ЖК в городе {city_name}.")
                return
            reply = f"Найдено в городе {city_name}:\n"
            for complex_name, complex_url in housing_complexes.items():
                reply += f"- {complex_name}: {complex_url}\n"
            await message.reply(reply)
            return

# Маршрут тестирования
async def test_handler(request):
    return web.json_response({"status": "ok", "message": "Test route is working!"})

# Маршрут для вебхука
async def handle_webhook(request):
    try:
        Bot.set_current(bot)  # Устанавливаем текущий экземпляр бота
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        update = types.Update(**data)
        await dp.process_update(update)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
    return web.Response(status=200)

# Настройка маршрутов
app.router.add_post("/test", test_handler)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

# Запуск приложения
if __name__ == "__main__":
    logger.info("Инициализация приложения...")
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")
    logger.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")
    web.run_app(app, host="0.0.0.0", port=PORT)
