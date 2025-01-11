import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
import requests
from bs4 import BeautifulSoup

# Telegram Bot Token
import os
API_TOKEN = os.getenv("API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Function to fetch and parse information about a housing complex
def fetch_housing_info(query):
    try:
        base_url = "https://ap-r.ru"
        visited_urls = set()  # Хранилище для уже посещённых страниц
        results = []

        def crawl_page(url):
            if url in visited_urls or len(visited_urls) > 100:  # Лимит на количество страниц
                return
            visited_urls.add(url)
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем карточки с ЖК
            complexes = soup.find_all('div', class_='complex-card')  # Настрой под реальную структуру сайта
            for complex_card in complexes:
                title = complex_card.find('h2').get_text(strip=True)
                if query.lower() in title.lower():
                    link = complex_card.find('a')['href']
                    results.append(f"🏢 {title}\n🔗 {base_url}{link}")

            # Ищем ссылки на другие страницы
            for link in soup.find_all('a', href=True):
                absolute_link = requests.compat.urljoin(base_url, link['href'])
                if base_url in absolute_link and absolute_link not in visited_urls:
                    crawl_page(absolute_link)

        # Запускаем парсинг с главной страницы
        crawl_page(base_url)

        if not results:
            return "Информация о данном жилом комплексе не найдена."
        return "\n\n".join(results[:5])  # Ограничиваем результат до 5 ЖК

    except Exception as e:
        logging.error(f"Ошибка при поиске информации: {e}")
        return "Произошла ошибка при обработке запроса."

# Command /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await message.reply("Привет! Я бот Ассоциации застройщиков. Напиши название жилого комплекса, чтобы получить информацию.")

# Handling user queries
@dp.message_handler()
async def search_housing(message: Message):
    query = message.text.strip()
    await message.reply("Ищу информацию, пожалуйста, подождите...")
    info = fetch_housing_info(query)
    await message.reply(info)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
