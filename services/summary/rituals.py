from .config import WEEKDAYS, parse_date


def ritual_is_for_date(ritual, target_date):
    if ritual.get("daily") is True:
        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):
        return False

    weekday_number = target_date.weekday()

    if weekday_number in days:
        return True

    weekday_name = WEEKDAYS[weekday_number]

    return weekday_name in days


def ritual_was_completed(ritual, target_date):
    completed_date = ritual.get("last_completed")

    if not completed_date:
        return False

    return parse_date(completed_date) == target_date

