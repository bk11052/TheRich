from datetime import datetime


def month_range(month: str) -> tuple[datetime, datetime]:
    """'YYYY-MM' → (해당 월 시작, 다음 달 시작). occurred_at 범위 필터용."""
    start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end
