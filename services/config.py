import os
import telebot
from supabase import create_client, Client

telebot.apihelper.ENABLE_MIDDLEWARE = True

# Зчитуємо змінні з Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Перевірка наявності змінних оточення
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ КРИТИЧНА ПОМИЛКА: В Render відсутні SUPABASE_URL або SUPABASE_KEY!")
    raise ValueError("Відсутні налаштування Supabase у змінних оточення.")

if not BOT_TOKEN:
    print("❌ КРИТИЧНА ПОМИЛКА: В Render відсутній BOT_TOKEN!")
    raise ValueError("Відсутній BOT_TOKEN у змінних оточення.")

print("✅ Змінні оточення успішно завантажені.")

# Створюємо екземпляри клієнтів
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

# Ігрові константи (шанси та лут)
LOOT_CHANCE = 0.003
POSSIBLE_LOOT = [
    "🧪 Настій Бадьорості",
    "📜 Стародавній Сувій",
    "💎 Кристал Натхнення",
    "🔑 Мідний Ключ"
]
