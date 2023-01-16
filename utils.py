from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Optional

import constants
from entities.portion_unit import BasePortionUnit, PortionUnit


def d2s(value: Decimal) -> str:
    return f'{round(value * 2) / 2:g}'


def normalize_statistic(statistic: dict):
    for key in constants.STATISTIC_KEYS:
        statistic[key] = d2s(statistic[key])


def format_date(date: datetime) -> str:
    return date.strftime(constants.DATE_FORMAT)


def parse_date(date: str) -> datetime:
    return datetime.strptime(date, constants.DATE_FORMAT)


def get_current_date() -> datetime:
    today = datetime.today() + timedelta(hours=-3)
    return today.replace(hour=0, minute=0, second=0, microsecond=0)


def parse_period(period: Optional[str]) -> Tuple[datetime, datetime, str]:
    current = get_current_date()

    if not period or period == "week":
        start_date = current + timedelta(days=-current.weekday())
        return start_date, start_date + timedelta(days=6), "week"

    if period == "today":
        return current, current, "today"

    if period == "yesterday":
        return current + timedelta(days=-1), current + timedelta(days=-1), "yesterday"

    if period == "last-week":
        start_date = current + timedelta(days=-7 - current.weekday())
        return start_date, start_date + timedelta(days=6), "last-week"

    if period == "last-14days":
        return current + timedelta(days=-13), current, "last-14days"

    start_date, end_date = period.split("-")
    start_date = parse_date(start_date) if start_date else current
    end_date = parse_date(end_date) if end_date else current

    if end_date > current:
        end_date = current

    return start_date, end_date, "period"


def get_dates_range(start_date: datetime, end_date: datetime, step: timedelta = timedelta(days=1)) -> List[datetime]:
    dates = []
    while start_date <= end_date:
        dates.append(start_date)
        start_date += step

    return dates


def get_default_portion(food_item: dict) -> Tuple[str, str]:
    conversions = {PortionUnit(unit): Decimal(str(value)) for unit, value in food_item["conversions"].items()}

    for portion_unit in (PortionUnit.portion, PortionUnit.piece, PortionUnit.slice):
        if portion_unit in conversions:
            return f'{portion_unit}', "1"

    base_unit = BasePortionUnit(food_item["portion"])
    if base_unit == BasePortionUnit.g100:
        return f'{PortionUnit.g}', "100"

    if base_unit == BasePortionUnit.ml100:
        return f'{PortionUnit.ml}', "100"

    raise ValueError(f"Unknown base unit \"{base_unit}\"")


def add_default_unit(food_items: list) -> list:
    for i, food_item in enumerate(food_items):
        default_unit, default_value = get_default_portion(food_item)
        food_items[i]["default_unit"] = default_unit
        food_items[i]["default_value"] = default_value

    return food_items
