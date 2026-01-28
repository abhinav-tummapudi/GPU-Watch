from datetime import timedelta

def convert_duration_to_seconds(duration: str) -> int:
    try:
        if "-" in duration:
            days, time_part = duration.split("-")
            days = int(days)
            parts = time_part.split(":")
        else:
            days = 0
            parts = duration.split(":")

        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
        elif len(parts) == 2:
            hours, minutes, seconds = 0, *map(int, parts)
        else:
            return 0

        return int(timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds())
    except Exception:
        return 0

