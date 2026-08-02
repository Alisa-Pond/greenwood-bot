from services.config import bot

@bot.message_handler(func=lambda message: message.text == "📜 Основний квест")
def main_quest_handler(message):
    bot.send_message(message.chat.id, "🔒 <b>Основний квест заблоковано.</b>", parse_mode="HTML")
