import os
import logging
import requests
from bs4 import BeautifulSoup
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
bot.set_current(bot)  # Установить текущий экземпляр бота
dp.middleware.setup(LoggingMiddleware())

# Функция парсинга данных
def parse_complex_info(query):
    try:
        base_url = "https://ap-r.ru"  # Базовый URL
        search_url = f"{base_url}/search?q={query}"  # URL для поиска
        response = requests.get(search_url)
        if response.status_code != 200:
            return "Ошибка: не удалось получить данные с сайта."

        soup = BeautifulSoup(response.text, "html.parser")
        # Найдите нужные элементы страницы (пример)
        results = soup.find_all("div", class_="complex-card")
        if not results:
            return "По вашему запросу ничего не найдено."

        info = []
        for result in results[:3]:  # Ограничиваем до 3 результатов
            name = result.find("h3").text.strip()
            link = base_url + result.find("a")["href"]
            description = result.find("p").text.strip()
            info.append(f"🏠 {name}\n{description}\nПодробнее: {link}")

        return "\n\n".join(info)
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return "Произошла ошибка при обработке запроса."

# Обработчик сообщений
@dp.message_handler()
async def send_complex_info(message: types.Message):
    query = message.text.strip()
    await message.reply("🔎 Ищу информацию, подождите...")
    info = parse_complex_info(query)
    await message.reply(info)

# Инициализация приложения Aiohttp
app = web.Application()

# Маршрут тестирования
async def test_handler(request):
    return web.json_response({"status": "ok", "message": "Тестовый маршрут работает!"})

# Маршрут для вебхука
async def handle_webhook(request):
    try:
        data = await request.json()
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
    web.run_app(app, host="0.0.0.0", port=PORT)
