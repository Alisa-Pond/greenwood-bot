
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from services.summary import send_daily_summaries


# =========================================================
# НАЛАШТУВАННЯ
# =========================================================

KYIV_TZ = ZoneInfo("Europe/Kyiv")

SUMMARY_HOUR = 7
SUMMARY_MINUTE = 0


# =========================================================
# ПЕРЕВІРКА ЧАСУ
# =========================================================

def is_summary_time():
    """
    Перевіряє, чи зараз 07:00 за київським часом.
    """

    now = datetime.now(KYIV_TZ)

    return (
        now.hour == SUMMARY_HOUR
        and now.minute == SUMMARY_MINUTE
    )


# =========================================================
# ЦИКЛ ПЛАНУВАЛЬНИКА
# =========================================================

def scheduler_loop():
    """
    Постійно перевіряє київський час.

    О 07:00 запускає формування
    та надсилання підсумків попередньої доби.

    Після запуску чекає, щоб не відправити
    підсумок повторно протягом тієї самої хвилини.
    """

    last_summary_date = None

    print("⏰ Планувальник підсумків запущено.")
    print("🌲 Часова зона: Europe/Kyiv")
    print("🌅 Щоденні підсумки: 07:00")


    while True:

        try:

            now = datetime.now(KYIV_TZ)

            current_date = now.date()


            # -------------------------------------------------
            # Чи настав час підсумків?
            # -------------------------------------------------

            if (
                now.hour == SUMMARY_HOUR
                and now.minute == SUMMARY_MINUTE
            ):

                # Захист від повторного запуску
                if last_summary_date != current_date:

                    print(
                        f"🌅 Настав час підсумків: "
                        f"{now.strftime('%d.%m.%Y %H:%M')}"
                    )

                    try:

                        send_daily_summaries()

                        last_summary_date = current_date

                        print(
                            "✅ Щоденні підсумки успішно відправлено."
                        )

                    except Exception as error:

                        print(
                            "❌ Помилка під час відправлення "
                            f"щоденних підсумків: {error}"
                        )

            # Перевіряємо час раз на 20 секунд
            time.sleep(20)


        except Exception as error:

            print(
                f"❌ Помилка планувальника: {error}"
            )

            # Якщо сталася помилка, не вбиваємо
            # весь процес Render.
            time.sleep(30)


# =========================================================
# ЗАПУСК У ФОНОВОМУ ПОТОЦІ
# =========================================================

def start_scheduler():
    """
    Запускає планувальник у окремому daemon-потоці.
    """

    thread = threading.Thread(
        target=scheduler_loop,
        daemon=True
    )

    thread.start()

    print("🌲 Фоновий планувальник Грінвуду працює.")

    return thread
