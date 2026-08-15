from services.config import bot
from services.database import get_all_players

from .player_summary import make_player_summary


def send_daily_summaries():
    print(
        "🌅 Починаю формування щоденних підсумків..."
    )

    players = get_all_players()

    if not players:
        print("ℹ️ Гравців для підсумку немає.")
        return

    sent = 0
    skipped = 0
    errors = 0

    for player_record in players:
        user_id = player_record.get("user_id")

        if not user_id:
            continue

        try:
            text = make_player_summary(user_id)

            if text is None:
                skipped += 1
                continue

            bot.send_message(
                int(user_id),
                text,
                parse_mode="HTML",
            )

            sent += 1

        except Exception as error:
            errors += 1

            print(
                f"❌ Не вдалося надіслати підсумок "
                f"{user_id}: {error}"
            )

    print(
        "🌅 Підсумки завершено. "
        f"Надіслано: {sent}; "
        f"пропущено: {skipped}; "
        f"помилок: {errors}."
    )

