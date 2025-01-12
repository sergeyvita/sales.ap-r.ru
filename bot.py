import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

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

# Инициализация приложения Aiohttp
app = web.Application()

# Маршрут тестирования
async def test_handler(request):
    logger.info("Получен запрос на тестовый маршрут")
    return web.json_response({"status": "ok", "message": "Test route is working!"})

# Маршрут для вебхука
async def handle_webhook(request):
    try:
        logger.info("Получен запрос на вебхук")
        data = await request.json()
        logger.info(f"Данные запроса: {data}")
        update = types.Update(**data)
        await dp.process_update(update)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
    return web.Response(status=200)

# Настройка маршрутов
app.router.add_post("/test", test_handler)  # Тестовый маршрут
app.router.add_post(WEBHOOK_PATH, handle_webhook)  # Вебхук маршрут

# Запуск приложения
if __name__ == "__main__":
    logger.info("Инициализация приложения...")
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")
    logger.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")
    logger.info("Зарегистрированные маршруты:")
    for route in app.router.routes():
        logger.info(f"Маршрут: {route.method} {route.resource}")

    web.run_app(app, host="0.0.0.0", port=PORT)
