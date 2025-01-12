import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://example.com")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"{WEBHOOK_HOST}{WEBHOOK_PATH}")
PORT = int(os.getenv("PORT", 5000))

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создание приложения aiohttp
app = web.Application()

# Временные тестовые маршруты
@app.post("/test")
async def test_endpoint(request):
    """Временный маршрут для проверки работы сервера."""
    data = await request.json()
    logger.info(f"Получен запрос на /test: {data}")
    return web.json_response({"status": "ok", "data": data})

@app.post(WEBHOOK_PATH)
async def handle_webhook(request):
    """Обработчик вебхука Telegram."""
    try:
        data = await request.json()
        logger.info(f"Получен запрос на вебхук: {data}")
        if "update_id" in data:
            # Здесь должна быть логика обработки обновлений Telegram
            return web.json_response({"status": "ok"})
        else:
            logger.warning("Неверный формат запроса!")
            return web.json_response({"error": "Invalid request format"}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return web.json_response({"error": "Internal Server Error"}, status=500)

@app.get("/")
async def home(request):
    """Главная страница для проверки работы приложения."""
    return web.Response(text="Бот работает, но это не вебхук!")

# Регистрация маршрутов и вывод списка
for route in app.router.routes():
    logger.info(f"Маршрут: {route.method} {route.resource}")

# Запуск приложения
if __name__ == "__main__":
    logger.info("Инициализация бота и диспетчера...")
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"ПОРТ: {PORT}")
    logger.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")
    logger.info("Запуск приложения...")
    web.run_app(app, host="0.0.0.0", port=PORT)
