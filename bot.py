import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import os
from collections import deque

# Telegram Bot Token
API_TOKEN = os.getenv("API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Base URL of the website
BASE_URL = "https://ap-r.ru"

# Function to fetch and parse information about a housing complex
async def fetch_housing_info(query):
    visited_urls = set()  # Tracks visited URLs
    results = []  # Stores results
    queue = deque([BASE_URL])  # Queue for BFS traversal

    async with ClientSession() as session:
        while queue and len(visited_urls) < 100:
            url = queue.popleft()
            if url in visited_urls:
                continue

            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        continue

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    visited_urls.add(url)

                    # Find housing complex cards (adjust based on actual site structure)
                    complexes = soup.find_all('div', class_='complex-card')
                    for complex_card in complexes:
                        title = complex_card.find('h2').get_text(strip=True)
                        if query.lower() in title.lower():
                            link = complex_card.find('a')['href']
                            results.append(f"🏢 {title}\n🔗 {BASE_URL}{link}")

                    # Find links to other pages
                    for link in soup.find_all('a', href=True):
                        absolute_link = aiohttp.helpers.URL(link['href']).join(BASE_URL)
                        if str(absolute_link).startswith(BASE_URL) and str(absolute_link) not in visited_urls:
                            queue.append(str(absolute_link))
            except Exception as e:
                logging.error(f"Error fetching URL {url}: {e}")

    if not results:
        return "Информация о данном жилом комплексе не найдена."
    return "\n\n".join(results[:5])  # Limit to 5 results

# Command /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await message.reply("Привет! Я бот Ассоциации застройщиков. Напиши название жилого комплекса, чтобы получить информацию.")

# Handling user queries
@dp.message_handler()
async def search_housing(message: Message):
    query = message.text.strip()
    await message.reply("Ищу информацию, пожалуйста, подождите...")
    info = await fetch_housing_info(query)
    await message.reply(info)

if __name__ == "__main__":
    # Start bot
    executor.start_polling(dp, skip_updates=True)
