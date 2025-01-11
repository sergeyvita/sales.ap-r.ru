import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.utils.executor import start_webhook
from aiohttp import web
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Конфигурация из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
PORT = int(os.getenv("PORT"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
BASE_URL = "https://ap-r.ru"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Асинхронные функции для загрузки и парсинга данных
async def fetch_page_content(url):
    """Загрузка содержимого страницы"""
    try:
        async with web.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Не удалось загрузить страницу: {url}")
                    return None
                return await response.text()
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы {url}: {e}")
        return None

def parse_cities(main_page_html):
    """Извлечение ссылок на города с главной страницы"""
    try:
        soup = BeautifulSoup(main_page_html, 'html.parser')
        city_links = soup.select('a.city-link')  # Измените селектор на актуальный
        return {link.text.strip(): urljoin(BASE_URL, link['href']) for link in city_links}
    except Exception as e:
        logger.error(f"Ошибка парсинга городов: {e}")
        return {}

def parse_complexes(city_page_html):
    """Извлечение информации о ЖК на странице города"""
    try:
        soup = BeautifulSoup(city_page_html, 'html.parser')
        complex_cards = soup.select('div.complex-card')  # Измените селектор на актуальный
        complexes = []
        for card in complex_cards:
            name = card.select_one('h2').text.strip()
            link = urljoin(BASE_URL, card.select_one('a')['href'])
            complexes.append({'name': name, 'link': link})
        return complexes
    except Exception as e:
        logger.error(f"Ошибка парсинга ЖК: {e}")
        return []

# Обработчики сообщений
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Напиши название жилого комплекса, чтобы я нашел информацию.")

@dp.message_handler()
async def handle_query(message: types.Message):
    query = message.text.strip()
    logger.info(f"Получен запрос: {query}")

    await message.reply("Ищу информацию, подождите...")

    main_page_html = await fetch_page_content(BASE_URL)
    if not main_page_html:
        await message.reply("Не удалось загрузить главную страницу сайта.")
        return

    cities = parse_cities(main_page_html)
    if not cities:
        await message.reply("Не удалось найти города на сайте.")
        return

    for city_name, city_url in cities.items():
        logger.info(f"Обрабатываю город: {city_name}, URL: {city_url}")
        city_page_html = await fetch_page_content(city_url)
        if not city_page_html:
            logger.warning(f"Не удалось загрузить страницу города: {city_name}")
            continue

        complexes = parse_complexes(city_page_html)
        for complex_ in complexes:
            if query.lower() in complex_['name'].lower():
                await message.reply(f"Найден ЖК: {complex_['name']}\nСсылка: {complex_['link']}")
                return

    await message.reply("Информация о данном жилом комплексе не найдена.")

# Вебхуки
async def handle_webhook(request):
    """Обработчик вебхука"""
    try:
        data = await request.json()
        update = Update.to_object(data)
        await dp.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(status=500)

# Запуск вебхуков
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(dp):
    await bot.delete_webhook()
    logger.info("Webhook удалён.")

# Создание веб-приложения
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
