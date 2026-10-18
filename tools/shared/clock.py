"""UAE business dates; an explicit DEMO_DATE can freeze local demonstrations."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from tools.shared.settings import settings


def now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Dubai"))


def today() -> date:
    return date.fromisoformat(settings.demo_date) if settings.demo_date else now().date()
