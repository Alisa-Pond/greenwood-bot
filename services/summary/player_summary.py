from datetime import datetime, timedelta

from services.database import get_player, update_player

from .archive import (
    calculate_earned_by_sphere,
    collect_completed_archive,
)
from .calculations import SPHERE_NAMES
from .config import KYIV, get_greenwood_date
from .missed import (
    empty_penalties,
    process_missed_plants,
    process_missed_rituals,
    process_missed_scrolls,
)
from .report import build_full_report


def make_player_summary(user_id):
    user_id = str(user_id)

    player = get_player(user_id)

    now = datetime.now(KYIV)

    current_date = get_greenwood_date(now)
    previous_date = current_date - timedelta(days=1)

    # -----------------------------------------------------
    # ЗАХИСТ ВІД ПОВТОРНОГО ПІДСУМКУ
    # -----------------------------------------------------

    statistics = player.get("statistics") or {}
    last_summary_date = statistics.get("last_summary_date")

    if last_summary_date == current_date.isoformat():
        return None

    # -----------------------------------------------------
    # АРХІВ ВИКОНАНИХ СПРАВ
    # -----------------------------------------------------

    scroll_archive = player.get("scroll_archive") or []
    ritual_archive = player.get("ritual_archive") or []
    plant_archive = player.get("plant_archive") or []

    completed_scrolls = collect_completed_archive(
        scroll_archive,
        previous_date,
    )

    completed_rituals = collect_completed_archive(
        ritual_archive,
        previous_date,
    )

    completed_plants = collect_completed_archive(
        plant_archive,
        previous_date,
    )

    completed_all = (
        completed_scrolls
        + completed_rituals
        + completed_plants
    )

    earned_by_sphere = calculate_earned_by_sphere(
        completed_all
    )

    # -----------------------------------------------------
    # ПРОПУЩЕНІ СПРАВИ
    # -----------------------------------------------------

    penalties_by_sphere = empty_penalties()

    missed_scrolls = process_missed_scrolls(
        player,
        current_date,
        penalties_by_sphere,
    )

    missed_rituals = process_missed_rituals(
        player,
        previous_date,
        penalties_by_sphere,
    )

    missed_plants = process_missed_plants(
        player,
        current_date,
        penalties_by_sphere,
    )

    missed_activities = (
        missed_scrolls
        + missed_rituals
        + missed_plants
    )

    # -----------------------------------------------------
    # ОНОВЛЮЄМО ДАТУ ОСТАННЬОГО ПІДСУМКУ
    # -----------------------------------------------------

    statistics = player.get("statistics") or {}
    statistics["last_summary_date"] = current_date.isoformat()
    player["statistics"] = statistics

    # -----------------------------------------------------
    # ЗБЕРІГАЄМО ЗМІНИ
    # -----------------------------------------------------

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "scrolls": player["scrolls"],
            "plants": player["plants"],
            "statistics": player["statistics"],
        },
    )

    # -----------------------------------------------------
    # ФОРМУЄМО ЗВІТ
    # -----------------------------------------------------

    return build_full_report(
        previous_date=previous_date,
        current_date=current_date,
        completed_scrolls=completed_scrolls,
        completed_rituals=completed_rituals,
        completed_plants=completed_plants,
        missed_activities=missed_activities,
        earned_by_sphere=earned_by_sphere,
        penalties_by_sphere=penalties_by_sphere,
        player=player,
    )

