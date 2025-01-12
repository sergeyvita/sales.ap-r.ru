import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiohttp import web
import os

# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

if not API_TOKEN or not WEBHOOK_URL:
    raise ValueError("Переменные окружения API_TOKEN или WEBHOOK_URL не установлены")

WEBHOOK_PATH = f"/webhook/{API_TOKEN}"

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Временный маршрут для тестирования
async def temporary_handler(request):
    logger.info("Получен временный запрос /test")
    return web.Response(text="Временный маршрут работает!", status=200)

# Обработчик вебхуков
async def handle_webhook(request):
    logger.info("Получен запрос вебхука")
    try:
        data = await request.json()
        logger.info(f"Данные запроса: {data}")
        update = Update.to_object(data)
        await dp.process_update(update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(text="Ошибка обработки вебхука", status=500)

# Базовый маршрут
async def index(request):
    logger.info("Получен запрос на /")
    return web.Response(text="Сервер работает!", status=200)

# Настройка приложения
app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/test", temporary_handler)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

logger.info("Зарегистрированные маршруты:")
for route in app.router.routes():
    logger.info(f"Маршрут: {route.method} {route.resource.canonical}")

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
