import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from bs4 import BeautifulSoup

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

# Заготовка данных для парсинга (загруженные страницы)
HTML_PAGES = {
    "Краснодар": "Краснодар.html",
    "Новороссийск": "Новороссийск.html",
    "Анапа": "Анапа.html",
    "Сочи и Архыз": "Сочи и Архыз.html",
    "Темрюк и Тамань": "Темрюк и Тамань.html",
    "Туапсинский район": "Туапсинский район.html",
    "Ростов-на-Дону": "Ростов-на-Дону.html",
    "Батайск": "Батайск.html",
    "Крым": "Крым.html",
    "Майкоп": "Майкоп.html",
}

# Функция для поиска ЖК
def find_housing_complex(city: str, complex_name: str):
    """Ищет информацию о жилом комплексе на соответствующей странице города."""
    file_name = HTML_PAGES.get(city)
    if not file_name:
        return f"Город '{city}' не найден в базе данных."

    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            # Пример: поиск карточки ЖК (заменить 'class_name' на реальный класс HTML-блока)
            cards = soup.find_all('div', class_='class_name')
            for card in cards:
                title = card.find('h3').text.strip()  # Заголовок ЖК
                if complex_name.lower() in title.lower():
                    description = card.find('p').text.strip()  # Описание ЖК
                    return f"ЖК: {title}\nОписание: {description}"
            return f"Жилой комплекс '{complex_name}' в городе '{city}' не найден."
    except Exception as e:
        logger.error(f"Ошибка парсинга файла {file_name}: {e}")
        return "Произошла ошибка при поиске информации. Попробуйте позже."

# Обработчик сообщений
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Привет! Я бот Ассоциации застройщиков. Введите запрос в формате:\nГород, ЖК Название")

@dp.message_handler()
async def handle_message(message: types.Message):
    try:
        query = message.text.split(',')  # Ожидаем формат: "Город, ЖК Название"
        if len(query) < 2:
            await message.reply("Введите запрос в формате: Город, ЖК Название")
            return

        city, complex_name = query[0].strip(), query[1].strip()
        response = find_housing_complex(city, complex_name)
        await message.reply(response)
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

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
app.router.add_post(WEBHOOK_PATH, handle_webhook)

# Запуск приложения
if __name__ == "__main__":
    logger.info("Инициализация приложения...")
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")
    logger.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")

    web.run_app(app, host="0.0.0.0", port=PORT)
