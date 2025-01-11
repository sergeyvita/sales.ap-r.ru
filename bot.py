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

# Base URL of the website
BASE_URL = "https://ap-r.ru"

# Function to fetch and parse information about a housing complex
def fetch_housing_info(query):
    try:
        # Search page or relevant logic for URL
        search_url = f"{BASE_URL}/search?q={query}"
        response = requests.get(search_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting housing complex details
        results = soup.find_all('div', class_='complex-card')  # Adjust to actual HTML structure
        if not results:
            return "Информация о данном жилом комплексе не найдена."

        info = []
        for result in results[:5]:  # Limit to top 5 results
            title = result.find('h2').text.strip()
            link = result.find('a')['href']
            info.append(f"🏢 {title}\n🔗 {BASE_URL}{link}")

        return "\n\n".join(info)

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
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
