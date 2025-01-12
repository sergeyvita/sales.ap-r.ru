import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from bs4 import BeautifulSoup
import requests

# Инициализация переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 5000))

# Логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Aiohttp приложение
app = web.Application()

# Главная страница сайта
BASE_URL = "https://ap-r.ru"


async def parse_cities():
    """Парсинг списка городов с главной страницы."""
    logger.debug("Начинаю парсинг списка городов из блока <select id='header_cities'>...")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    city_select = soup.find("select", {"id": "header_cities"})

    cities = {}
    if city_select:
        options = city_select.find_all("option")
        for option in options:
            city_name = option.text.strip()
            city_url = BASE_URL + option["value"]
            if city_name != "Город не выбран":
                cities[city_name] = city_url
                logger.debug(f"Найдена ссылка на город: {city_name} -> {city_url}")
    logger.info(f"Итоговый список городов: {cities}")
    return cities


async def find_complex(city_url, query):
    """Поиск ЖК или МКР на странице города."""
    logger.debug(f"Начинаю поиск ЖК или МКР '{query}' на странице {city_url}...")
    response = requests.get(city_url)
    soup = BeautifulSoup(response.text, "html.parser")
    objects = soup.find_all("div", class_="object-tile-content-detail match-height")

    for obj in objects:
        title = obj.find("a", class_="object-tile-title").text.strip()
        if query.lower() in title.lower():
            details_url = BASE_URL + obj.find("a", class_="object-tile-title")["href"]
            logger.debug(f"Найден объект: {title} -> {details_url}")
            return title, details_url
    return None, None


async def fetch_complex_details(details_url):
    """Извлечение информации о ЖК или МКР."""
    logger.debug(f"Парсинг информации о ЖК/МКР со страницы {details_url}...")
    response = requests.get(details_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Извлекаем название ЖК
    title = soup.find("h2", class_="default-h2").text.strip()

    # Извлекаем описание
    description_block = soup.find("div", class_="croptext-content")
    description = description_block.get_text(strip=True) if description_block else "Описание отсутствует."

    logger.debug(f"Данные о ЖК/МКР: {title} - {description}")
    return title, description


@dp.message_handler()
async def handle_message(message: types.Message):
    """Обработчик сообщений от пользователя."""
    query = message.text.strip()
    logger.info(f"Получен запрос на поиск ЖК: '{query}' от пользователя {message.from_user.id}")

    await message.reply(f"Ищу информацию о ЖК/МКР '{query}'...")

    try:
        # Парсинг городов
        cities = await parse_cities()

        # Поиск ЖК в каждом городе
        for city_name, city_url in cities.items():
            logger.debug(f"Ищу ЖК/МКР '{query}' в городе {city_name} ({city_url})")
            title, details_url = await find_complex(city_url, query)

            if details_url:
                # Получение деталей ЖК/МКР
                title, description = await fetch_complex_details(details_url)

                # Разделяем длинный текст на части
                max_length = 4000  # Ограничение длины сообщения
                parts = [description[i:i + max_length] for i in range(0, len(description), max_length)]

                # Отправляем части по очереди
                for part in parts:
                    await message.reply(part)

                return

        # Если ЖК/МКР не найден
        await message.reply(f"ЖК/МКР '{query}' не найден. Попробуйте уточнить запрос.")

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.reply("Произошла ошибка при поиске. Попробуйте позже.")


async def handle_webhook(request):
    """Обработка вебхуков."""
    data = await request.json()
    logger.info(f"Получен вебхук: {data}")
    update = types.Update(**data)
    await dp.process_update(update)
    return web.Response(status=200)


async def on_startup(app):
    """Действия при старте."""
    logger.info("Установка вебхука...")
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(app):
    """Действия при завершении."""
    logger.info("Удаление вебхука...")
    await bot.delete_webhook()


# Настройка маршрутов
app.router.add_post(WEBHOOK_PATH, handle_webhook)

# Настройка старта и завершения приложения
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Запуск приложения
if __name__ == "__main__":
    logger.info("Запуск приложения...")
    web.run_app(app, host="0.0.0.0", port=PORT)
