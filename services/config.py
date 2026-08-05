import os
import telebot
print("✅ telebot імпортовано")
from supabase import create_client, Client
print("✅ supabase імпортовано")
telebot.apihelper.ENABLE_MIDDLEWARE = True

# Зчитуємо змінні з Render
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# 🔍 Діагностика ключів у логах
print("--- ДІАГНОСТИКА ЗМІННИХ ---")
if SUPABASE_URL:
    print(f"🌐 SUPABASE_URL: {SUPABASE_URL[:15]}... (довжина: {len(SUPABASE_URL)})")
else:
    print("❌ SUPABASE_URL відсутній!")

if SUPABASE_KEY:
    print(f"🔑 SUPABASE_KEY: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:]} (довжина: {len(SUPABASE_KEY)})")
else:
    print("❌ SUPABASE_KEY відсутній!")

if BOT_TOKEN:
    print(f"🤖 BOT_TOKEN: {BOT_TOKEN[:10]}... (довжина: {len(BOT_TOKEN)})")
else:
    print("❌ BOT_TOKEN відсутній!")
print("----------------------------")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Відсутні налаштування Supabase у змінних оточення.")

if not BOT_TOKEN:
    raise ValueError("Відсутній BOT_TOKEN у змінних оточення.")

# Створюємо клієнти
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Клієнт Supabase успішно створено!")
except Exception as e:
    print(f"💥 Помилка при підключенні до Supabase: {e}")
    raise e

bot = telebot.TeleBot(BOT_TOKEN)

LOOT_CHANCE = 0.003
POSSIBLE_LOOT = [
    "🧪 Настій Бадьорості",
    "📜 Стародавній Сувій",
    "💎 Кристал Натхнення",
    "🔑 Мідний Ключ"
]
