import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiohttp import web
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
PORT = int(os.getenv("PORT", 5000))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
BASE_URL = "https://ap-r.ru"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await message.reply("Бот запущен. Напишите название ЖК для поиска.")

# Обработчик сообщений (поиск ЖК)
@dp.message_handler()
async def handle_message(message: types.Message):
    query = message.text.strip()
    logger.info(f"Получен запрос: {query}")
    await message.reply("Ищу информацию, пожалуйста, подождите...")

    # Пример обработки запроса
    main_page_html = await fetch_page_content(BASE_URL)
    if not main_page_html:
        await message.reply("Не удалось загрузить главную страницу.")
        return
    
    # Извлечение данных (здесь можно реализовать парсинг ЖК)
    # Например, cities = parse_cities(main_page_html)

    await message.reply(f"Информация о '{query}' не найдена.")

# Функция для загрузки содержимого страницы
async def fetch_page_content(url):
    try:
        async with web.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы {url}: статус {response.status}")
                    return None
                return await response.text()
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы {url}: {e}")
        return None

# Веб-приложение
app = web.Application()

# Тестовый маршрут для проверки
async def index(request):
    return web.Response(text="Сервер работает!")

app.router.add_get("/", index)

# Обработчик вебхуков
async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.to_object(data)
        await dp.process_update(update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(text="Ошибка обработки вебхука", status=500)

app.router.add_post(WEBHOOK_PATH, handle_webhook)

# Запуск приложения
if __name__ == "__main__":
    logging.info(f"API_TOKEN: {API_TOKEN}")
    logging.info(f"WEBHOOK_HOST: {WEBHOOK_HOST}")
    logging.info(f"PORT: {PORT}")
    logging.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    web.run_app(app, host="0.0.0.0", port=PORT)
