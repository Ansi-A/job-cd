from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import logging

def get_next_scheduled_time(time_str: str, tz_string: str) -> datetime:
    """
    Finds the next occurrence of a specific time (e.g. "09:00") in the user's timezone,
    and returns it as a UTC datetime object for database storage.
    """
    try:
        user_tz = ZoneInfo(tz_string)
    except Exception:
        logging.warning(f"Invalid timezone '{tz_string}'. Falling back to UTC.")
        user_tz = ZoneInfo("UTC")

    # 1. What time is it right now in the user's timezone?
    now_local = datetime.now(user_tz)

    # 2. Parse the target hour and minute
    target_hour, target_minute = map(int, time_str.split(":"))

    # 3. Create "today at 9:00 AM" in the user's timezone
    target_time_local = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    # 4. If 9:00 AM already passed today, push it to tomorrow
    if now_local >= target_time_local:
        target_time_local += timedelta(days=1)

    # 5. Convert to Universal Time (UTC) to save in the database
    utc_time = target_time_local.astimezone(ZoneInfo("UTC"))

    return utc_time