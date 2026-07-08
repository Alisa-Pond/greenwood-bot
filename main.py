import telebot
from telebot import types
import os
from threading import Thread
from flask import Flask

# Створюємо мікро-веб-сервер, щоб Render думав, що це сайт і не вимикав бота
app = Flask('')

@app.route('/')
def home():
    return "Greenwood Chronicles is alive!"

def run_server():
    # Render сам дає порт через змінні оточення
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Підключаємо бота (ВСТАВ СВІЙ ТОКЕН НИЖЧЕ ЗАМІСТЬ ТВІЙ_ТОКЕН_СЮДИ)
bot = telebot.TeleBot("8952936471:AAELfnR9M933B_XfPQseJtpvVNPDt7yilmA")

player_stats = {
    "health": 0,
    "knowledge": 0,
    "boss_hp": 100
}

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("🐸 Мій Статус у Лісі")
    btn_run = types.KeyboardButton("🏃‍♂️ Побігав (+10 Здоров'я)")
    btn_read = types.KeyboardButton("📚 Почитав (+5 Знань)")
    markup.add(btn_status)
    markup.add(btn_run, btn_read)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "🌲 **Ласкаво просимо до Greenwood Chronicles!** 🌲\n\n"
        "Я — Lilly Pond, твій магічний провідник у цьому затишному лісі. "
        "Тут твої щоденні звички перетворюються на справжню магію!\n\n"
        "👾 На околицях лісу з'явився перший бос — **Лінивий Слиз** (100 HP).\n"
        "Виконуй свої реальні завдання, розвивай сфери життя та допомагай мені очистити ліс!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.message_handler(content_types=['text'])
def handle_gameplay(message):
    global player_stats
    if message.text == "🐸 Мій Статус у Лісі":
        status_report = (
            "🧙‍♂️ **Твій Персонаж:**\n"
            f"❤️ Сфера Здоров'я: {player_stats['health']} очок\n"
            f"🧠 Сфера Знань: {player_stats['knowledge']} очок\n\n"
            f"⚔️ **Поточна битва:**\n"
            f"👾 Бос (Лінивий Слиз): {player_stats['boss_hp']}/100 HP"
        )
        bot.send_message(message.chat.id, status_report, parse_mode="Markdown")
    elif message.text == "🏃‍♂️ Побігав (+10 Здоров'я)":
        player_stats["health"] += 10
        player_stats["boss_hp"] -= 10
        bot.send_message(message.chat.id, "🐸 *Lilly Pond радісно квакає!* Ти додав +10 до Здоров'я і завдав 10 урону босу!", parse_mode="Markdown")
        check_boss_defeat(message)
    elif message.text == "📚 Почитав (+5 Знань)":
        player_stats["knowledge"] += 5
        player_stats["boss_hp"] -= 5
        bot.send_message(message.chat.id, "✨ *Магия знань у дії!* Ти отримав +5 до Знань і завдав 5 урону босу!", parse_mode="Markdown")
        check_boss_defeat(message)

def check_boss_defeat(message):
    global player_stats
    if player_stats["boss_hp"] <= 0:
        victory_text = (
            "🎉 **УРА! БОСА ПОДОЛАНО!** 🎉\n\n"
            "Лінивий Слиз розчистився у магічному сяйві. Lilly Pond пишається твоєю дисципліною!\n"
            "🎁 *Твоя нагорода:* Час для заслуженого відпочинку! Виконай обіцянку, яку дав собі перед цим боєм."
        )
        bot.send_message(message.chat.id, victory_text, parse_mode="Markdown")
        player_stats["boss_hp"] = 100

# Запуск веб-сервера в окремому потоці
Thread(target=run_server).start()

# Запуск бота
bot.polling(none_stop=True)