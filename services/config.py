import os
import telebot
from supabase import create_client, Client

telebot.apihelper.ENABLE_MIDDLEWARE = True

# Зчитуємо змінні з Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Перевірка наявності змінних
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ КРИТИЧНА ПОМИЛКА: В Render відсутні SUPABASE_URL або SUPABASE_KEY!")
else:
    print("✅ SUPABASE конфігурацію знайдено.")

if not BOT_TOKEN:
    print("❌ КРИТИЧНА ПОМИЛКА: В Render відсутній BOT_TOKEN!")
else:
    print("✅ BOT_TOKEN знайдено.")

# Створюємо клієнти
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

# Шанс випадіння луту та можливі предмети
LOOT_CHANCE = 0.003
POSSIBLE_LOOT = [
    "🧪 Настій Бадьорості",
    "📜 Стародавній Сувій",
    "💎 Кристал Натхнення",
    "🔑 Мідний Ключ"
]
