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

BASE_URL = "https://ap-r.ru"

# Инициализация логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Инициализация приложения Aiohttp
app = web.Application()

# Функция для парсинга ссылок на города
def get_city_links():
    logger.debug("Начинаю парсинг списка городов...")
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug("Успешно получен HTML главной страницы")

        # Ищем ссылки на города
        city_links = {}
        for link in soup.find_all("a"):
            href = link.get("href", "")
            if "/goroda/" in href:  # Проверяем, что ссылка ведет на город
                city_name = link.text.strip()
                city_url = BASE_URL + href
                city_links[city_name] = city_url
                logger.debug(f"Найдена ссылка на город: {city_name} -> {city_url}")

        logger.info(f"Итоговый список городов: {city_links}")
        return city_links
    except Exception as e:
        logger.error(f"Ошибка парсинга городов: {e}")
        return {}

# Функция для поиска информации о ЖК
def find_residential_complex(city_url, complex_name):
    logger.debug(f"Начинаю поиск ЖК '{complex_name}' в городе по URL: {city_url}")
    try:
        response = requests.get(city_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug(f"Успешно получен HTML для города: {city_url}")

        # Ищем ЖК
        for complex_card in soup.find_all("div", class_="complex-card"):  # Укажите реальный класс для карточки ЖК
            name = complex_card.find("h2").text.strip()  # Укажите реальный тег/класс для названия ЖК
            logger.debug(f"Проверяю ЖК: {name}")
            if complex_name.lower() in name.lower():
                description = complex_card.find("p").text.strip()  # Описание ЖК
                url = complex_card.find("a").get("href", "")  # Ссылка на ЖК
                logger.info(f"Найден ЖК: {name} -> {BASE_URL + url}")
                return f"ЖК: {name}\nОписание: {description}\nПодробнее: {BASE_URL + url}"
        logger.debug(f"ЖК '{complex_name}' не найден в городе по URL: {city_url}")
        return "ЖК с указанным названием не найден."
    except Exception as e:
        logger.error(f"Ошибка при поиске ЖК: {e}")
        return "Ошибка при поиске информации о ЖК."

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.reply("Добро пожаловать! Напишите название ЖК, чтобы получить информацию.")

# Обработчик текстовых сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    user_query = message.text.strip()
    logger.info(f"Получен запрос на поиск ЖК: '{user_query}' от пользователя {message.from_user.id}")
    await message.reply(f"Ищу информацию о ЖК '{user_query}'...")
    
    # Получаем список городов
    city_links = get_city_links()
    if not city_links:
        logger.error("Список городов пуст. Ошибка парсинга.")
        await message.reply("Не удалось получить список городов. Попробуйте позже.")
        return

    # Ищем ЖК по всем городам
    for city_name, city_url in city_links.items():
        logger.debug(f"Ищу ЖК '{user_query}' в городе {city_name} ({city_url})")
        result = find_residential_complex(city_url, user_query)
        if "ЖК с указанным названием не найден" not in result:
            await message.reply(result)
            logger.info(f"ЖК '{user_query}' найден в городе {city_name}")
            return

    logger.info(f"ЖК '{user_query}' не найден ни в одном городе.")
    await message.reply("ЖК с указанным названием не найден. Убедитесь, что ввели название правильно.")

# Маршрут тестирования
async def test_handler(request):
    logger.info("Получен запрос на тестовый маршрут.")
    return web.json_response({"status": "ok", "message": "Test route is working!"})

# Маршрут для вебхука
async def handle_webhook(request):
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
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
