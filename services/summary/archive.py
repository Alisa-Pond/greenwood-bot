from .calculations import get_spheres, get_title, get_xp
from .config import SPHERE_NAMES, parse_date


def collect_completed_archive(archive, previous_date):
    completed = []

    for item in archive or []:
        completed_date = parse_date(
            item.get("completed_date")
        )

        if completed_date != previous_date:
            continue

        completed.append(item)

    return completed


def calculate_earned_by_sphere(items):
    earned_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    for item in items:
        xp = get_xp(item)
        spheres = get_spheres(item)

        if not spheres:
            continue

        share = xp / len(spheres)

        for sphere in spheres:
            if sphere in earned_by_sphere:
                earned_by_sphere[sphere] += share

    return earned_by_sphere

