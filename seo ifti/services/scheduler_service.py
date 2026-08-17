"""
SEO Scheduler Service: Algorithmic Best Practice Optimal Posting Engine for Socials OS.
"""

from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Tuple

# Weekdays: Monday = 0, Tuesday = 1, Wednesday = 2, Thursday = 3, Friday = 4, Saturday = 5, Sunday = 6
# Optimal posting windows based on algorithmic engagement data:
ALGORITHMIC_WINDOWS: Dict[str, List[Tuple[int, int, int]]] = {
    # platform: list of (weekday, hour_24, minute)
    "linkedin": [
        (1, 9, 0),   # Tuesday 9:00 AM
        (2, 9, 0),   # Wednesday 9:00 AM
        (3, 9, 0),   # Thursday 9:00 AM
    ],
    "tiktok": [
        (1, 19, 0),  # Tuesday 7:00 PM
        (3, 19, 0),  # Thursday 7:00 PM
        (5, 20, 0),  # Saturday 8:00 PM (Bonus high-traffic weekend window)
    ],
    "instagram": [
        (2, 18, 0),  # Wednesday 6:00 PM
        (4, 18, 0),  # Friday 6:00 PM
        (0, 11, 0),  # Monday 11:00 AM
    ],
    "twitter": [
        (0, 8, 0),   # Monday 8:00 AM
        (2, 12, 0),  # Wednesday 12:00 PM
        (4, 9, 0),   # Friday 9:00 AM
    ],
    "youtube": [
        (3, 15, 0),  # Thursday 3:00 PM (indexation window before evening binge)
        (4, 15, 0),  # Friday 3:00 PM
        (5, 10, 0),  # Saturday 10:00 AM
    ],
    "facebook": [
        (0, 13, 0),  # Monday 1:00 PM
        (2, 13, 0),  # Wednesday 1:00 PM
        (4, 13, 0),  # Friday 1:00 PM
    ],
}


def get_optimal_post_time(platform: str, base_time: Optional[datetime] = None) -> datetime:
    """
    Calculates the next upcoming algorithmic optimal posting time for a given platform.
    Ensures posts are not fired immediately, but queued for maximum organic reach.
    """
    platform_key = platform.lower().strip()
    if platform_key in ["x", "x/twitter", "x_twitter"]:
        platform_key = "twitter"

    slots = ALGORITHMIC_WINDOWS.get(
        platform_key,
        [(1, 10, 0), (3, 14, 0), (4, 16, 0)]  # Default mid-week morning slots
    )

    if base_time is None:
        current = datetime.now(timezone.utc)
    else:
        current = base_time if base_time.tzinfo else base_time.replace(tzinfo=timezone.utc)

    # Search the next 14 days for the nearest future slot
    candidate_times: List[datetime] = []
    for day_offset in range(0, 14):
        check_date = current.date() + timedelta(days=day_offset)
        check_weekday = check_date.weekday()

        for slot_weekday, hour, minute in slots:
            if check_weekday == slot_weekday:
                candidate_dt = datetime.combine(
                    check_date,
                    time(hour=hour, minute=minute),
                    tzinfo=current.tzinfo or timezone.utc,
                )
                # Slot must be at least 30 minutes in the future
                if candidate_dt > current + timedelta(minutes=30):
                    candidate_times.append(candidate_dt)

    if candidate_times:
        candidate_times.sort()
        return candidate_times[0]

    # Fallback to tomorrow at 9 AM
    tomorrow = current.date() + timedelta(days=1)
    return datetime.combine(tomorrow, time(9, 0), tzinfo=current.tzinfo or timezone.utc)


def calculate_all_optimal_times(base_time: Optional[datetime] = None) -> Dict[str, str]:
    """Generates optimal ISO formatted times for all 6 major networks."""
    platforms = ["facebook", "instagram", "linkedin", "twitter", "youtube", "tiktok"]
    return {p: get_optimal_post_time(p, base_time).isoformat() for p in platforms}
