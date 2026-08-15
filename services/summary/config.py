from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KYIV = ZoneInfo("Europe/Kyiv")

SPHERE_NAMES = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝",
}

WEEKDAYS = [
    "пн",
    "вт",
    "ср",
    "чт",
    "пт",
    "сб",
    "нд",
]


def get_greenwood_date(dt=None):
    if dt is None:
        dt = datetime.now(KYIV)

    if dt.hour < 7:
        dt -= timedelta(days=1)

    return dt.date()


def format_date(date):
    return date.strftime("%d.%m.%Y")


def parse_date(value):
    if not value:
        return None

    if hasattr(value, "date"):
        return value.date()

    if not isinstance(value, str):
        return None

    value = value.strip()

    for fmt in ("%d.%m.%y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None

