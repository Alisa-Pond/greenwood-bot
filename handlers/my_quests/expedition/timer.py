from datetime import datetime, timezone

from services.config import bot
from services.database import get_player, update_player

from handlers.my_quests.expedition.menu import get_active_expedition


print("⏱️ Реєструємо таймер експедицій...")


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ ЧАСУ
# =========================================================

def get_now():
    """
    Повертає поточний час UTC.
    """

    return datetime.now(
        timezone.utc
    )


def parse_datetime(value):
    """
    Перетворює ISO-рядок у datetime.
    """

    if not value:
        return None

    try:

        dt = datetime.fromisoformat(
            value
        )

        # Якщо старий запис не має timezone,
        # вважаємо його UTC.

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:

        return None


# =========================================================
# РОЗРАХУНОК АКТИВНОГО ЧАСУ
# =========================================================

def calculate_active_seconds(expedition):
    """
    Повертає загальну кількість секунд,
    проведених саме в активній частині експедиції.

    Привал не враховується.
    """

    saved_seconds = int(
        expedition.get(
            "active_seconds",
            0
        ) or 0
    )

    status = expedition.get(
        "status",
        "active"
    )

    # -----------------------------------------------------
    # Якщо експедиція зараз на привалі
    # -----------------------------------------------------

    if status == "paused":

        return saved_seconds

    # -----------------------------------------------------
    # Якщо експедиція активна
    # -----------------------------------------------------

    last_resumed_at = parse_datetime(
        expedition.get(
            "last_resumed_at"
        )
    )

    if not last_resumed_at:

        return saved_seconds

    now = get_now()

    current_session_seconds = int(
        (
            now - last_resumed_at
        ).total_seconds()
    )

    if current_session_seconds < 0:

        current_session_seconds = 0

    return (
        saved_seconds
        + current_session_seconds
    )


# =========================================================
# ФОРМАТУВАННЯ ЧАСУ
# =========================================================

def format_expedition_time(seconds):
    """
    Перетворює секунди у зручний текст.
    """

    seconds = int(
        seconds or 0
    )

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    remaining_seconds = (
        seconds % 60
    )

    if hours > 0:

        return (
            f"{hours} год "
            f"{minutes} хв"
        )

    if minutes > 0:

        return (
            f"{minutes} хв"
        )

    return (
        f"{remaining_seconds} сек"
    )


# =========================================================
# 🏕️ ЗРОБИТИ ПРИВАЛ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🏕️ Зробити привал"
)
def pause_expedition(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    expedition = get_active_expedition(
        player
    )

    # -----------------------------------------------------
    # Немає експедиції
    # -----------------------------------------------------

    if not expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Генерал не бачить поблизу жодного "
                "експедиційного загону."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Вже на привалі
    # -----------------------------------------------------

    if expedition.get(
        "status"
    ) == "paused":

        bot.send_message(
            message.chat.id,
            (
                "🏕️ <b>Генерал Мураха:</b>\n\n"
                "Загін уже відпочиває біля вогнища.\n\n"
                "Не хвилюйся, жодна хвилина привалу "
                "не загубить прогрес експедиції."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Зберігаємо накопичений час
    # -----------------------------------------------------

    active_seconds = calculate_active_seconds(
        expedition
    )

    now = get_now()

    expedition["active_seconds"] = (
        active_seconds
    )

    expedition["status"] = "paused"

    expedition["paused_at"] = (
        now.isoformat()
    )

    # -----------------------------------------------------
    # Оновлюємо базу
    # -----------------------------------------------------

    success = update_player(
        user_id,
        {
            "expeditions": [
                expedition
            ]
        }
    )

    if not success:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Виникла проблема з журналом експедиції. "
                "Привал не вдалося зареєструвати."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Повідомлення
    # -----------------------------------------------------

    time_text = format_expedition_time(
        active_seconds
    )

    bot.send_message(
        message.chat.id,
        (
            "🏕️ <b>Генерал Мураха доповідає:</b>\n\n"

            "Загін зупинився для привалу.\n"
            "Мурахи розклали карти, перевірили "
            "запаси та трохи перепочивають.\n\n"

            f"⏱️ Активний час експедиції: "
            f"<b>{time_text}</b>\n\n"

            "Таймер зупинено. "
            "Коли будеш готова продовжити, "
            "натисни <b>▶️ Продовжити експедицію</b>."
        ),
        parse_mode="HTML"
    )


# =========================================================
# ▶️ ПРОДОВЖИТИ ЕКСПЕДИЦІЮ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "▶️ Продовжити експедицію"
)
def resume_expedition(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    expedition = get_active_expedition(
        player
    )

    # -----------------------------------------------------
    # Немає експедиції
    # -----------------------------------------------------

    if not expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Схоже, цей загін уже повернувся "
                "з експедиції."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Експедиція вже активна
    # -----------------------------------------------------

    if expedition.get(
        "status"
    ) == "active":

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Загін уже в дорозі.\n"
                "Мурахи не можуть вирушити двічі "
                "одночасно."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Зберігаємо новий час старту
    # -----------------------------------------------------

    now = get_now()

    expedition["status"] = "active"

    expedition["last_resumed_at"] = (
        now.isoformat()
    )

    expedition["paused_at"] = None

    # -----------------------------------------------------
    # Оновлюємо базу
    # -----------------------------------------------------

    success = update_player(
        user_id,
        {
            "expeditions": [
                expedition
            ]
        }
    )

    if not success:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Не вдалося передати загону "
                "наказ про продовження."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Повідомлення
    # -----------------------------------------------------

    time_text = format_expedition_time(
        expedition.get(
            "active_seconds",
            0
        )
    )

    bot.send_message(
        message.chat.id,
        (
            "🐜 <b>Генерал Мураха доповідає:</b>\n\n"

            "Загін зібрав спорядження "
            "і знову вирушив у путь.\n\n"

            f"⏱️ Накопичений активний час: "
            f"<b>{time_text}</b>\n\n"

            "🧭 Дослідження Грінвуду продовжується."
        ),
        parse_mode="HTML"
    )


# =========================================================
# 🏁 ЗАВЕРШИТИ ЕКСПЕДИЦІЮ
# =========================================================
#
# Тут ми поки НЕ завершуємо експедицію самостійно.
#
# Логіка завершення буде в complete.py.
#
# Це зроблено навмисно, щоб:
#
# timer.py
#     → відповідав за час
#
# complete.py
#     → відповідав за завершення
#
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🏁 Завершити експедицію"
)
def request_expedition_completion(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    expedition = get_active_expedition(
        player
    )

    if not expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Експедиційний загін уже повернувся "
                "або ще не був відправлений."
            ),
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # Передаємо керування complete.py
    # -----------------------------------------------------

    from handlers.my_quests.expedition.complete import (
        complete_expedition
    )

    complete_expedition(
        message
    )


# =========================================================
# ПЕРЕВІРКА 60-ХВИЛИННИХ НАГАДУВАНЬ
# =========================================================

def check_expedition_reminder(
    player
):
    """
    Перевіряє, чи настав час нагадати користувачу
    про активну експедицію.

    Функція НЕ запускає окремий таймер.

    Її можна викликати із scheduler.py.
    """

    user_id = str(
        player.get(
            "user_id"
        )
    )

    expedition = get_active_expedition(
        player
    )

    if not expedition:

        return False

    if expedition.get(
        "status"
    ) != "active":

        return False

    active_seconds = calculate_active_seconds(
        expedition
    )

    # -----------------------------------------------------
    # Скільки повних годин минуло
    # -----------------------------------------------------

    completed_hours = (
        active_seconds // 3600
    )

    if completed_hours < 1:

        return False

    last_reminder = int(
        expedition.get(
            "last_reminder_minute",
            0
        ) or 0
    )

    current_reminder_minute = (
        completed_hours * 60
    )

    # -----------------------------------------------------
    # Не надсилаємо повторно
    # -----------------------------------------------------

    if current_reminder_minute <= last_reminder:

        return False

    # -----------------------------------------------------
    # Оновлюємо позначку нагадування
    # -----------------------------------------------------

    expedition["last_reminder_minute"] = (
        current_reminder_minute
    )

    update_player(
        user_id,
        {
            "expeditions": [
                expedition
            ]
        }
    )

    # -----------------------------------------------------
    # Надсилаємо нагадування
    # -----------------------------------------------------

    time_text = format_expedition_time(
        active_seconds
    )

    try:

        bot.send_message(
            int(user_id),
            (
                "🐜 <b>Генерал Мураха доповідає:</b>\n\n"

                "Загін уже досить довго мандрує "
                "стежками Грінвуду.\n\n"

                f"⏱️ Активний час експедиції: "
                f"<b>{time_text}</b>\n\n"

                "Мурахи продовжують пошуки, "
                "але вирішили нагадати командуванню, "
                "що їх досі не повернули. 🐜\n\n"

                "Якщо ти вже завершила свої справи, "
                "не забудь повернути загін."
            ),
            parse_mode="HTML"
        )

        return True

    except Exception as error:

        print(
            "❌ Не вдалося надіслати "
            "нагадування експедиції:"
        )

        print(error)

        return False
