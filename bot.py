import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiohttp import web, ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

if not API_TOKEN or not WEBHOOK_URL:
    raise ValueError("Необходимые переменные окружения API_TOKEN или WEBHOOK_URL не установлены")

WEBHOOK_PATH = "/webhook"
BASE_URL = "https://ap-r.ru"  # URL сайта для парсинга

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
logger.info("Инициализация бота и диспетчера...")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Асинхронная загрузка содержимого страницы
async def fetch_page_content(url):
    """Загрузка содержимого страницы."""
    logger.info(f"Загрузка страницы: {url}")
    try:
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка загрузки страницы: {url} (Статус {response.status})")
                    return None
                return await response.text()
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы {url}: {e}")
        return None

# Парсинг городов
def parse_cities(main_page_html):
    """Извлечение ссылок на города с главной страницы."""
    try:
        soup = BeautifulSoup(main_page_html, 'html.parser')
        city_links = soup.select('a.city-link')  # Обновите селектор на актуальный
        cities = {link.text.strip(): urljoin(BASE_URL, link['href']) for link in city_links}
        logger.info(f"Найдены города: {list(cities.keys())}")
        return cities
    except Exception as e:
        logger.error(f"Ошибка парсинга городов: {e}")
        return {}

# Парсинг ЖК
def parse_complexes(city_page_html):
    """Извлечение информации о ЖК на странице города."""
    try:
        soup = BeautifulSoup(city_page_html, 'html.parser')
        complex_cards = soup.select('div.complex-card')  # Обновите селектор на актуальный
        complexes = []
        for card in complex_cards:
            name = card.select_one('h2').text.strip()
            link = urljoin(BASE_URL, card.select_one('a')['href'])
            complexes.append({'name': name, 'link': link})
        logger.info(f"Найдено ЖК: {[c['name'] for c in complexes]}")
        return complexes
    except Exception as e:
        logger.error(f"Ошибка парсинга ЖК: {e}")
        return []

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    logger.info("Получена команда /start")
    await message.reply("Бот запущен. Напишите название ЖК для поиска.")
    logger.info("Ответ отправлен пользователю")

# Обработчик сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    query = message.text.strip()
    logger.info(f"Получено сообщение от пользователя: {query}")
    await message.reply("Ищу информацию, подождите...")

    # Загрузка главной страницы
    main_page_html = await fetch_page_content(BASE_URL)
    if not main_page_html:
        await message.reply("Ошибка: не удалось загрузить главную страницу сайта.")
        return

    # Парсинг городов
    cities = parse_cities(main_page_html)
    if not cities:
        await message.reply("Не удалось найти города на сайте.")
        return

    # Поиск ЖК
    for city_name, city_url in cities.items():
        logger.info(f"Обрабатываю город: {city_name}")
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

# Обработчик вебхуков
async def handle_webhook(request):
    try:
        logger.info("Получен запрос вебхука")
        data = await request.json()
        logger.info(f"Полученные данные вебхука: {data}")
        update = Update.to_object(data)
        await dp.process_update(update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(text="Ошибка обработки вебхука", status=500)

# Базовый маршрут для проверки сервиса
async def index(request):
    logger.info("Получен запрос на маршрут /")
    return web.Response(text="Сервер работает!")

# Настройка приложения
app = web.Application()
app.router.add_get("/", index)
app.router.add_post(WEBHOOK_PATH, handle_webhook)

# Запуск приложения
if __name__ == "__main__":
    logger.info(f"API_TOKEN: {API_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")
    logger.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")

    try:
        logger.info("Запуск приложения...")
        web.run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
