import re
from decimal import Decimal
from typing import Optional, List, Dict, Tuple

import requests
from bs4 import BeautifulSoup, Tag

import constants
from entities.food_item import FoodItem
from entities.portion_unit import BasePortionUnit, PortionUnit


class FatSecretParser:
    def parse(self, url: str) -> Optional[FoodItem]:
        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            return None

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find("div", {"class": "nutrition_facts"})

        if not div:
            return None

        texts = self.__get_div_texts(div)
        try:
            title = soup.find("title")
            name = re.sub(r"\s+Калории и Пищевая Ценность", "", title.text)
            portion, conversions, scale = self.__get_portion_info(texts[-13].replace(",", "."))
            energy = self.__round(Decimal(texts[-9].split(' ')[0]) * scale)
            fats = self.__round(Decimal(texts[-7][:-1].replace(',', '.')) * scale)
            carbohydrates = self.__round(Decimal(texts[-5][:-1].replace(',', '.')) * scale)
            cellulose = self.__round(Decimal(texts[-3][:-1].replace(',', '.')) * scale)
            proteins = self.__round(Decimal(texts[-1][:-1].replace(',', '.')) * scale)

            food = FoodItem("", name, "", energy, fats, proteins, carbohydrates, portion, conversions)
            return food
        except ValueError:
            return None

    def parse_search(self, query: str, page: int = 0) -> List[dict]:
        try:
            response = requests.get(f'http://fatsecret.ru/калории-питание/search?q={query}&pg={page}')
        except requests.exceptions.ConnectionError:
            return []

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"class": "searchResult"})

        if not table:
            return []

        results = []

        for td in table.find_all("td"):
            name = td.find("a", {"class": "prominent"})
            brand = td.find("a", {"class": "brand"})
            brand = brand.get_text() if brand else ""
            small_text = td.find("div", {"class": "smallText"})
            small_text = re.match(r'в[\s\S]*Белк: \d+(,\d+)?г', small_text.get_text().strip()).group()
            results.append({
                "link": f'http://fatsecret.ru/{name["href"]}',
                "name": f'{name.get_text()}{brand}',
                "info": small_text
            })

        return results

    def __round(self, value: Decimal) -> Decimal:
        if value < Decimal("10"):
            scale = 100
        elif value < Decimal("1000"):
            scale = 10
        else:
            scale = 2

        return Decimal(str(int(value * scale) / scale))

    def __get_div_texts(self, div: Tag) -> List[str]:
        texts = [d.text.strip() for d in div if d.text.strip()]
        texts_filtered = []
        labels = ["Белки", "Жиры", "Углеводы", "Клетчатка"]

        for i, text in enumerate(texts):
            if i < 7:
                texts_filtered.append(text)
            elif text in labels or texts_filtered[-1] in labels:
                texts_filtered.append(text)

        assert re.fullmatch(r"Размер Порции", texts_filtered[-14])
        assert re.fullmatch(r"\d+ ккал", texts_filtered[-9])
        assert re.fullmatch(r"Жиры", texts_filtered[-8])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-7])
        assert re.fullmatch(r"Углеводы", texts_filtered[-6])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-5])
        assert re.fullmatch(r"Клетчатка", texts_filtered[-4])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-3])
        assert re.fullmatch(r"Белки", texts_filtered[-2])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-1])

        return texts_filtered

    def __replace_unit(self, unit: str) -> str:
        if re.fullmatch(rf'{"|".join(constants.SLICE_NAMES)}', unit):
            return "ломтик"

        if re.fullmatch(rf'{"|".join(constants.PORTION_NAMES)}', unit):
            return "порция"

        return "шт"

    def __get_portion_info(self, portion_text: str) -> Tuple[BasePortionUnit, Dict[PortionUnit, Decimal], Decimal]:
        conversions = dict()

        if portion_text in [BasePortionUnit.g100, BasePortionUnit.ml100]:
            return BasePortionUnit(portion_text), conversions, Decimal("1")

        if portion_text in ["100g (100 г)"]:
            return BasePortionUnit.g100, conversions, Decimal("1")

        if portion_text in ["100г (100 мл)"]:
            conversions[PortionUnit.ml] = Decimal("0.01")
            return BasePortionUnit.g100, conversions, Decimal("1")

        match = re.match(rf"^(?P<count>\d+) +(?P<unit>\w+(?: \w+)*) +\((?P<value>\d+(.\d*)?) г\)$", portion_text)
        if match:
            count, unit, value = Decimal(match.group("count")), self.__replace_unit(match.group("unit")), match.group("value")
            scale = Decimal("100") / Decimal(value)
            conversions[PortionUnit(unit)] = Decimal(value) / count / Decimal("100")
            return BasePortionUnit.g100, conversions, scale

        match = re.match(rf"^100г +\((?P<value>\d+(.\d*)?) г\)$", portion_text)
        if match:
            value = match.group("value")
            scale = Decimal("100") / Decimal(value)
            conversions[PortionUnit.portion] = Decimal(value) / Decimal("100")
            return BasePortionUnit.g100, conversions, scale

        match = re.match(r"^1 +(?P<unit>порция) +\((?P<value>\d+(.\d*)?) мл\)$", portion_text)
        if match:
            unit, value = match.group("unit"), match.group("value")
            scale = Decimal("100") / Decimal(value)
            conversions[PortionUnit(unit)] = Decimal(value) / Decimal("100")
            return BasePortionUnit.ml100, conversions, scale

        raise ValueError(f'Invalid portion description: "{portion_text}"')
