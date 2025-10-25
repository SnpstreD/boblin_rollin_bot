import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env file")

BOT_CONFIG = {
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
}
