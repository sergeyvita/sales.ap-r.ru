import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiohttp import web, ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

if not API_TOKEN or not WEBHOOK_URL:
    raise ValueError("Необходимые переменные окружения API_TOKEN или WEBHOOK_URL не установлены")

WEBHOOK_PATH = "/webhook"
BASE_URL = "https://ap-r.ru"  # URL сайта для парсинга

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
logger.info("Инициализация бота и диспетчера...")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Временный тестовый обработчик для всех запросов
async def temporary_handler(request):
    logger.info("Получен временный запрос")
    try:
        data = await request.json()
        logger.info(f"Данные запроса: {data}")
        return web.Response(text="Вебхук получен!", status=200)
    except Exception as e:
        logger.error(f"Ошибка временного обработчика: {e}")
        return web.Response(text="Ошибка обработки", status=500)

# Асинхронная загрузка содержимого страницы
async def fetch_page_content(url):
    logger.info(f"Загрузка страницы: {url}")
    try:
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы: {url} (Статус {response.status})")
                    return None
                return await response.text()
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы {url}: {e}")
        return None

# Обработчик вебхуков
async def handle_webhook(request):
    try:
        logger.info("Получен запрос вебхука")
        data = await request.json()
        logger.info(f"Полученные данные вебхука: {data}")
        update = Update.to_object(data)
        await dp.process_update(update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(text="Ошибка обработки вебхука", status=500)

# Базовый маршрут для проверки сервиса
async def index(request):
    logger.info("Получен запрос на маршрут /")
    return web.Response(text="Сервер работает!")

# Настройка приложения
app = web.Application()
app.router.add_get("/", index)
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.router.add_post("/test", temporary_handler)  # Временный маршрут для тестов

# Запуск приложения
if __name__ == "__main__":
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")
    logger.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")

    try:
        logger.info("Запуск приложения...")
        web.run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
