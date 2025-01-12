import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiohttp import web
from bs4 import BeautifulSoup
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Переменные окружения
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 5000))

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

# Обработчик сообщений
@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот Ассоциации застройщиков. Напишите название ЖК или МКР, чтобы получить информацию.")

@dp.message_handler()
async def handle_message(message: types.Message):
    query = message.text.strip()
    logger.info(f"Получен запрос на поиск ЖК: '{query}' от пользователя {message.from_user.id}")

    try:
        await message.reply(f"Ищу информацию о ЖК/МКР '{query}'...")
        
        # Парсинг главной страницы
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ap-r.ru") as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Парсим список городов
                cities = {}
                select = soup.find("select", id="header_cities")
                if select:
                    for option in select.find_all("option"):
                        if option.get("value") and option["value"] != "/":
                            cities[option.text.strip()] = f"https://ap-r.ru{option['value']}"

                logger.info(f"Итоговый список городов: {cities}")

                # Ищем ЖК/МКР в каждом городе
                for city_name, city_url in cities.items():
                    logger.debug(f"Ищу ЖК/МКР '{query}' в городе {city_name} ({city_url})")
                    async with session.get(city_url) as city_response:
                        city_html = await city_response.text()
                        city_soup = BeautifulSoup(city_html, "html.parser")

                        # Ищем блок ЖК/МКР
                        tiles = city_soup.find_all("div", class_="object-tile-content-detail match-height")
                        for tile in tiles:
                            title_tag = tile.find("a", class_="object-tile-title")
                            if title_tag and query.lower() in title_tag.text.lower():
                                full_url = f"https://ap-r.ru{title_tag['href']}"
                                logger.info(f"Найден ЖК/МКР: {title_tag.text.strip()} -> {full_url}")
                                
                                # Получение деталей ЖК/МКР
                                async with session.get(full_url) as details_response:
                                    details_html = await details_response.text()
                                    details_soup = BeautifulSoup(details_html, "html.parser")
                                    description = details_soup.find("div", class_="croptext-content")
                                    description_text = description.get_text(strip=True) if description else "Описание отсутствует."
                                    await message.reply(f"Найден ЖК/МКР: {title_tag.text.strip()}\n{description_text}")
                                return

        # Если ЖК/МКР не найден
        await message.reply(f"ЖК/МКР '{query}' не найден. Попробуйте уточнить запрос.")
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.reply("Произошла ошибка при поиске. Попробуйте позже.")

# Настройка вебхука
async def on_startup(dp):
    logger.info("Установка вебхука...")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logger.info("Удаление вебхука...")
    await bot.delete_webhook()

# Запуск приложения
if __name__ == "__main__":
    from aiogram import executor
    logger.info("Запуск приложения...")
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True, host="0.0.0.0", port=PORT)
