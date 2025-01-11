import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Telegram Bot Token
API_TOKEN = os.getenv("API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Base URL of the website
BASE_URL = "https://ap-r.ru"

async def fetch_cities():
    """
    Fetch all city links from the main page.
    """
    async with ClientSession() as session:
        async with session.get(BASE_URL) as response:
            if response.status != 200:
                logging.error("Failed to load main page")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all city links (adjust the class or structure as needed)
            city_links = soup.find_all('a', href=True, class_='city-link')  # Adjust class name
            cities = [urljoin(BASE_URL, link['href']) for link in city_links]
            return cities

async def fetch_housing_info(city_url, query):
    """
    Fetch housing information from a specific city's page.
    """
    async with ClientSession() as session:
        async with session.get(city_url) as response:
            if response.status != 200:
                logging.error(f"Failed to load city page: {city_url}")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            # Find housing complex cards (adjust based on actual site structure)
            complexes = soup.find_all('div', class_='complex-card')  # Adjust class name
            results = []
            for complex_card in complexes:
                title = complex_card.find('h2').get_text(strip=True)
                if query.lower() in title.lower():
                    link = complex_card.find('a')['href']
                    results.append(f"🏢 {title}\n🔗 {urljoin(BASE_URL, link)}")
            
            return results

@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await message.reply("Привет! Я бот Ассоциации застройщиков. Напиши название жилого комплекса, чтобы получить информацию.")

@dp.message_handler()
async def search_housing(message: Message):
    query = message.text.strip()
    await message.reply("Ищу информацию, пожалуйста, подождите...")

    # Fetch city links
    city_links = await fetch_cities()
    if not city_links:
        await message.reply("Не удалось получить список городов.")
        return

    results = []
    for city_url in city_links:
        city_results = await fetch_housing_info(city_url, query)
        results.extend(city_results)
        if results:  # Stop searching if we already found results
            break

    if not results:
        await message.reply("Информация о данном жилом комплексе не найдена.")
    else:
        await message.reply("\n\n".join(results[:5]))  # Limit to 5 results

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
