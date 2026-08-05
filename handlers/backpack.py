from services.config import bot
from services.database import get_player

print("⚙️ Реєструємо хендлер рюкзака...")

@bot.message_handler(func=lambda message: message.text == "🎒 Рюкзак")
def show_inventory(message):
    user_id = str(message.from_user.id)
    current_player = get_player(user_id)
    inventory = current_player.get("inventory", [])
    
    if not inventory:
        bot.send_message(
            message.chat.id,
            "🎒 <b>Твій рюкзак порожній. Час здобути трофеї!</b>",
            parse_mode="HTML"
        )
    else:
        items_counts = {}

        for item in inventory:
            items_counts[item] = items_counts.get(item, 0) + 1
        
        inv_text = "🎒 <b>Вміст твого рюкзака:</b>\n\n"

        for item, count in items_counts.items():
            inv_text += f"• {item} x{count}\n"

        bot.send_message(
            message.chat.id,
            inv_text,
            parse_mode="HTML"
        )
