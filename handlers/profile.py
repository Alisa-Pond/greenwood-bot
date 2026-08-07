import time
import logging
import traceback

from services.config import bot
from services.database import get_player
from keyboards import get_main_menu


logger = logging.getLogger(__name__)


print("⚙️ Реєструємо хендлери профілю...")


# =========================
# /START
# =========================

@bot.message_handler(commands=['start'])
def welcome(message):

    print("#################################")
    print("START СПРАЦЮВАВ")
    print(message.from_user.id)
    print("#################################")

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    print(player)

    try:

        user_id = str(message.from_user.id)
        player = get_player(user_id)

        msg_1 = (
            "🌲 <b>Вітаю у Грінвуді!</b> 🌳\n\n"
            "Я - 🪷 <b>Lilly Pond</b> 🪷! "
            "Сиджу на лататті, гріюся на сонечку "
            "й збираю найгарячіші плітки цього магічного лісу.\n\n"
            "Кажуть, ти тут, щоб перетворити свої реальні справи "
            "на справжній левелап? ✨"
        )

        bot.send_message(
            message.chat.id,
            msg_1,
            parse_mode="HTML"
        )

        time.sleep(2)


        msg_2 = (
            "🔮 <b>Як працює Грінвуд:</b>\n\n"

            "Твій персонаж розвиває 5 сфер сили:\n\n"

            "💪 <b>Здоров'я</b> — спорт, сон, харчування.\n"
            "🧠 <b>Мудрість</b> — навчання, книги, нові навички.\n"
            "🎨 <b>Творчість</b> — мистецтво, музика, ідеї.\n"
            "💵 <b>Фінанси</b> — робота, бюджет, розвиток.\n"
            "🤝 <b>Зв'язки</b> — близькі люди, турбота, спілкування.\n\n"

            "📜 У <b>Моїх квестах</b> ти створюєш свої завдання:\n"
            "сувої, ритуали, рослини та майбутні експедиції.\n\n"

            "✨ А кнопка <b>Виконати справу</b> допомагає "
            "перетворити зроблене у реальному житті на XP."
        )


        bot.send_message(
            message.chat.id,
            msg_2,
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
    except Exception:

        print("❌ ПОМИЛКА START:")
        print(traceback.format_exc())
# =========================
# ПЕРСОНАЖ
# =========================

@bot.message_handler(
    func=lambda message: message.text == "🧙‍♂️ Персонаж"
)
def show_profile(message):

    user_id = str(message.from_user.id)

    current_player = get_player(user_id)


    status = (
        f"🧙‍♂️ <b>Лист персонажа "
        f"(Рівень {current_player.get('level', 1)})</b>\n\n"
    )

    status += (
        f"✨ Загальний досвід: "
        f"{float(current_player.get('xp_total', 0)):.1f} XP\n"
    )

    status += "────────────────────\n"


    spheres = current_player.get("spheres", {})


    for key, sphere in spheres.items():

        status += (
            f"{sphere['name']}: "
            f"Лвл {sphere['lvl']} "
            f"({float(sphere['xp']):.1f}/"
            f"{float(sphere['max_xp']):.1f} XP)\n"
        )


    bot.send_message(
        message.chat.id,
        status,
        parse_mode="HTML"
    )
