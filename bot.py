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
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BASE_URL = "https://ap-r.ru"

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
logger.info("Инициализация бота и диспетчера...")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    logger.info("Получена команда /start")
    await message.reply("Бот запущен. Напишите название ЖК для поиска.")
    logger.info("Ответ отправлен пользователю")

# Обработчик сообщений (поиск ЖК)
@dp.message_handler()
async def handle_message(message: types.Message):
    query = message.text.strip()
    logger.info(f"Получен текстовый запрос: {query}")
    await message.reply("Ищу информацию, пожалуйста, подождите...")

    main_page_html = await fetch_page_content(BASE_URL)
    if not main_page_html:
        logger.error("Не удалось загрузить главную страницу.")
        await message.reply("Не удалось загрузить главную страницу.")
        return
    
    logger.info("Главная страница успешно загружена.")
    await message.reply(f"Информация о '{query}' не найдена.")
    logger.info(f"Информация о запросе '{query}' не найдена.")

# Функция для загрузки содержимого страницы
async def fetch_page_content(url):
    try:
        logger.info(f"Загрузка содержимого страницы: {url}")
        async with web.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы {url}: статус {response.status}")
                    return None
                logger.info(f"Содержимое страницы {url} успешно загружено")
                return await response.text()
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы {url}: {e}")
        return None

# Веб-приложение
app = web.Application()

# Тестовый маршрут для проверки
async def index(request):
    logger.info("Получен запрос на маршрут /")
    return web.Response(text="Сервер работает!")

app.router.add_get("/", index)

# Обработчик вебхуков
async def handle_webhook(request):
    try:
        logger.info("Получен запрос вебхука")
        data = await request.json()
        logger.info(f"Полученные данные: {data}")
        update = Update.to_object(data)
        await dp.process_update(update)
        logger.info("Вебхук успешно обработан")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(text="Ошибка обработки вебхука", status=500)

app.router.add_post(WEBHOOK_URL.split("/")[-1], handle_webhook)

# Запуск приложения
if __name__ == "__main__":
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")
    try:
        logger.info("Запуск приложения...")
        web.run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
