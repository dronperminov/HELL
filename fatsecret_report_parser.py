import re
from datetime import datetime
import csv
from typing import Tuple, Optional, Dict, List

from entities.portion_unit import PortionUnit
from decimal import Decimal


class FatSecretReportParser:
    def __init__(self):
        self.months = {
            "января": 1,
            "февраля": 2,
            "марта": 3,
            "апреля": 4,
            "мая": 5,
            "июня": 6,
            "июля": 7,
            "августа": 8,
            "сентября": 9,
            "октября": 10,
            "ноября": 11,
            "декабря": 12
        }

    def parse(self, path: str) -> Dict[datetime, Dict[str, List[dict]]]:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()

        data = self.__parse_lines(lines)

        for date in data:
            for meal_type, meals in data[date].items():
                assert len(meals) % 2 == 0
                parsed_meal = []

                for i in range(0, len(meals), 2):
                    try:
                        parsed_meal.append(self.__parse_meal(meals[i], meals[i + 1]))
                    except ValueError:
                        pass

                data[date][meal_type] = parsed_meal

        return data

    def __parse_lines(self, lines: List[str]) -> Dict[datetime, Dict[str, dict]]:
        curr_date = None
        curr_meal_type = None
        data = {}

        for line in lines:
            if not line:
                curr_date = None
                curr_meal_type = None
                continue

            if re.match(r'^"(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье), \w+ \d\d?, \d{4}"', line):
                curr_date = self.__parse_date(line)
                data[curr_date] = {}
                continue

            if re.match(r' (Завтрак|Обед|Ужин|Перекус/Другое),', line):
                curr_meal_type = line.split(',')[0].strip()
                data[curr_date][curr_meal_type] = []
                continue

            if curr_date is None or curr_meal_type is None:
                continue

            data[curr_date][curr_meal_type].append(line)

        return data

    def __parse_date(self, line: str) -> datetime:
        weekday, month, day, year = re.split(r",? ", line.split('"')[1])
        return datetime(int(year), self.months[month], int(day))

    def __parse_portion(self, portion: str) -> Optional[Tuple[Decimal, PortionUnit]]:
        if re.fullmatch(r"\d+ (г|мл)", portion):
            portion_size, portion_unit = portion.split(" ")
            return Decimal(portion_size), PortionUnit(portion_unit)

        if re.fullmatch(r"[\d/ x]+ порция, \d+ г", portion):
            portion_size = Decimal(portion.split(" ")[-2])
            return portion_size, PortionUnit.g

        if re.fullmatch(r"\d+ ч.л.", portion):
            portion_size = Decimal(portion.split(" ")[0])
            return portion_size, PortionUnit.tea_spoon

        if re.fullmatch(r"\d+/\d+ ч.л.", portion):
            a, b = portion.split(" ")[0].split("/")
            portion_size = Decimal(a) / Decimal(b)
            return portion_size, PortionUnit.tea_spoon

        if re.fullmatch(r"[\d/ x\w]+, \d+([.,]\d+)? г", portion):
            portion_size = Decimal(portion.split(" ")[-2].replace(",", "."))
            return portion_size, PortionUnit.g

        return None

    def __parse_meal(self, line1: str, line2: str) -> dict:
        args1 = list(csv.reader([line1]))[0]
        args2 = list(csv.reader([line2]))[0]

        name = re.sub(r"\s+", " ", args1[0].strip())
        portion = args2[0].strip()
        parsed_portion = self.__parse_portion(portion)

        if parsed_portion is None:
            print(f"ERROR: {name}", portion)
            raise ValueError("Invalid portion")

        meal = {
            "energy": Decimal(args1[1].replace(",", ".")),
            "proteins": Decimal(args1[7].replace(",", ".")),
            "fats": Decimal(args1[2].replace(",", ".")),
            "carbohydrates": Decimal(args1[4].replace(",", ".")),
            "portion_size": parsed_portion[0],
            "portion_unit": parsed_portion[1],
            "name": name,
        }

        return meal
