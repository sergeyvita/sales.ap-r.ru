import os
import logging
import requests
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook
from bs4 import BeautifulSoup

# Инициализация переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 5000))
BASE_URL = "https://ap-r.ru"  # Главная страница сайта

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
Bot.set_current(bot)  # Устанавливаем текущий экземпляр бота в контексте

# Функция для получения списка городов
def get_city_links():
    logger.debug("Начинаю парсинг списка городов из блока <select id='header_cities'>...")
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        html_content = response.text
        logger.debug(f"HTML главной страницы:\n{html_content[:500]}...")  # Логируем первые 500 символов HTML

        soup = BeautifulSoup(html_content, "html.parser")
        logger.debug("Успешно получен HTML главной страницы")

        # Ищем тег <select id="header_cities">
        select_tag = soup.find("select", id="header_cities")
        if not select_tag:
            logger.error("Не найден блок <select id='header_cities'> на главной странице.")
            return {}

        # Извлекаем все <option> внутри <select>
        city_links = {}
        for option in select_tag.find_all("option"):
            city_name = option.text.strip()
            city_url = option["value"].strip()

            # Пропускаем опцию "Город не выбран" или некорректные ссылки
            if city_url == "/" or not city_url.startswith("/"):
                continue

            # Формируем полный URL города
            full_url = BASE_URL + city_url
            city_links[city_name] = full_url
            logger.debug(f"Найдена ссылка на город: {city_name} -> {full_url}")

        logger.info(f"Итоговый список городов: {city_links}")
        return city_links
    except Exception as e:
        logger.error(f"Ошибка парсинга городов: {e}")
        return {}

# Обработчик вебхуков
async def handle_webhook(request):
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        update = types.Update(**data)
        await dp.process_update(update)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
    return web.Response(status=200)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Напиши название ЖК, и я постараюсь найти информацию о нем.")

# Обработчик текстовых сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    user_query = message.text.strip()
    logger.info(f"Получен запрос на поиск ЖК: '{user_query}' от пользователя {message.from_user.id}")
    await message.reply(f"Ищу информацию о ЖК '{user_query}'...")

    # Получаем список городов
    city_links = get_city_links()
    if not city_links:
        await message.reply("Не удалось получить список городов. Попробуйте позже.")
        return

    # Пытаемся найти ЖК
    for city_name, city_url in city_links.items():
        try:
            response = requests.get(city_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Ищем ЖК на странице города
            complex_blocks = soup.find_all("div", class_="complex-card")  # Примерный класс для блоков ЖК
            for block in complex_blocks:
                title = block.find("h3").text.strip()
                if user_query.lower() in title.lower():
                    details = block.find("p").text.strip()
                    await message.reply(f"Найден ЖК '{title}' в городе {city_name}:\n{details}\nПодробнее: {city_url}")
                    return
        except Exception as e:
            logger.error(f"Ошибка парсинга города {city_name}: {e}")
            continue

    await message.reply(f"ЖК '{user_query}' не найден. Попробуйте уточнить запрос.")

# Тестовый маршрут
async def test_handler(request):
    return web.json_response({"status": "ok", "message": "Test route is working!"})

# Настройка маршрутов
app = web.Application()
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
