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

        msg_1 = (
            "🌲 <b>Грінвуд помітив тебе.</b>\n\n"
            "Ти не знаєш, як саме опинився тут.\n"
            "Лише пам'ятаєш стежку між деревами, "
            "запах моху після дощу й дивне відчуття, "
            "ніби ліс давно на тебе чекав.\n\n"

            "🪷 <b>Lilly Pond</b> 🪷\n"
            "«Нарешті! Я вже почала думати, що ти заблукав.\n\n"

            "Я — Лілі Понд. Мешканка цього ставка, "
            "збирачка новин і, якщо вірити деяким особливо "
            "образливим стрикозам, головна пліткарка всього Грінвуду.»\n\n"
        )

        bot.send_message(
            message.chat.id,
            msg_1,
            parse_mode="HTML"
        )

        time.sleep(2)

        msg_2 = (
            "🪷 <b>Lilly Pond</b> 🪷\n"
            "«Грінвуд трохи дивний. Тут твої звичайні справи "
            "можуть перетворитися на магію.\n\n"

            "Ти можеш розвивати 5 сфер свого персонажа:\n\n"

            "💪 <b>Здоров'я</b> - спорт, турбота про себе, харчування...\n"
            "🧠 <b>Мудрість</b> - навчання, читання, нові навички...\n"
            "🎨 <b>Творчість</b> — мистецтво, музика, ідеї...\n"
            "💵 <b>Фінанси</b> — робота, гроші...\n"
            "🤝 <b>Зв'язки</b> — люди, допомога іншим, спілкування...\n\n"

            "Використову розділ власних квестів для документування своїх  виконань\n"
            "📜 <b>Сувої</b> — одноразові справи, які ти хочеш виконати.\n"
            "🔄 <b>Ритуали</b> — справи, які мають повторюватися.\n"
            "🌱 <b>Рослини</b> — довгострокові цілі, які ти вирощуєш.\n"
            "🧭 <b>Експедиції</b> — час зосередженої роботи або навчання.\n\n"

            "А все, що ти робиш у реальному житті, "
            "може приносити тобі XP, розвиток сфер "
            "і навіть несподівані знахідки.» ✨"
        )

        bot.send_message(
            message.chat.id,
            msg_2,
            parse_mode="HTML"
        )

        time.sleep(2)

        msg_3 = (
            "🪷 <b>Lilly Pond</b> 🪷\n"
            "«Але є ще дещо.\n\n"

            "🌲 <b>Грінвуд має для тебе основний квест.</b>\n\n"

            "«Тож ласкаво просимо до Грінвуду.\n"
            "Ліс відкривається лише тому, хто наважується йти далі.\n "
            "Тож зроби перший крок.\n\n"
        )

        bot.send_message(
            message.chat.id,
            msg_3,
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
        f"(Рівень {current_player.get('level', 1)})</b>\n"
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
