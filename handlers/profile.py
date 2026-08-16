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

            "Попереду тихо хлюпає вода.\n"
            "На поверхні ставка погойдується латаття.\n\n"

            "🪷 <b>Lilly Pond</b> 🪷\n"
            "«Нарешті! Я вже почала думати, що ти заблукав.\n\n"

            "Не хвилюйся, я тебе проведу. Ну... "
            "принаймні поки не знайду когось цікавішого, "
            "про кого можна поговорити.» 👀\n\n"

            "«Я — Лілі Понд. Мешканка цього ставка, "
            "збирачка новин і, якщо вірити деяким особливо "
            "образливим жабам, головна пліткарка всього Грінвуду.\n\n"

            "Але ти запам'ятай одне: у цьому лісі майже нічого "
            "не відбувається просто так.»"
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

            "Ти розвиватимеш п'ять сфер свого персонажа:\n\n"

            "💪 <b>Здоров'я</b> — спорт, сон, харчування.\n"
            "🧠 <b>Мудрість</b> — навчання, книги, нові навички.\n"
            "🎨 <b>Творчість</b> — мистецтво, музика, ідеї.\n"
            "💵 <b>Фінанси</b> — робота, гроші, розвиток.\n"
            "🤝 <b>Зв'язки</b> — люди, турбота, спілкування.\n\n"

            "📜 <b>Сувої</b> — одноразові справи, які ти хочеш виконати.\n"
            "🔄 <b>Ритуали</b> — справи, які мають повторюватися.\n"
            "🌱 <b>Рослини</b> — довгострокові цілі, які ти вирощуєш.\n"
            "🧭 <b>Експедиції</b> — час зосередженої роботи або навчання.\n\n"

            "«А все, що ти робиш у реальному житті, "
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

            "Це не просто список справ. "
            "Ліс поступово відкриватиметься перед тобою, "
            "а разом із ним — його мешканці, таємниці, місця "
            "й історії.\n\n"

            "Щоб просуватися сюжетом, тобі доведеться "
            "виконувати завдання, які даватиме сам Грінвуд.\n\n"

            "Деякі приведуть тебе до нових місць.\n"
            "Деякі — до нових мешканців.\n"
            "А деякі... краще навіть не питай мене заздалегідь. 👀\n\n"

            "«Тож ласкаво просимо до Грінвуду.\n"
            "Тримай очі відкритими, не довіряй кожній жабі "
            "і головне — не пропускай цікаві плітки.\n\n"

            "Можеш починати. Я все одно вже знаю, "
            "що ти робитимеш далі.» 🪷"
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
