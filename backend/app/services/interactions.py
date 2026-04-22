from datetime import datetime


def calculate_duration_minutes(start_time: datetime, end_time: datetime) -> int:
    delta = end_time - start_time
    minutes = int(delta.total_seconds() // 60)
    if minutes < 0:
        raise ValueError("End time cannot be before start time")
    return minutes
