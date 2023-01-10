from typing import Optional, List, Dict

import requests
from bs4 import BeautifulSoup, Tag
import re
from decimal import Decimal

from entities.food_item import FoodItem
from entities.portion_unit import BasePortionUnit, PortionUnit


class FatSecretParser:
    def parse(self, url: str) -> Optional[FoodItem]:
        response = requests.get(url)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find("title")
        name = title.text.replace(" Калории и Пищевая Ценность", "")

        div = soup.find("div", {"class": "nutrition_facts"})
        texts = self.__get_div_texts(div)

        energy = Decimal(texts[-7].split(' ')[0])
        fats = Decimal(texts[-5][:-1].replace(',', '.'))
        carbohydrates = Decimal(texts[-3][:-1].replace(',', '.'))
        proteins = Decimal(texts[-1][:-1].replace(',', '.'))

        portion_text = texts[-11].replace(",", ".")
        portion = BasePortionUnit.from_str(portion_text)
        conversions = self.__get_conversions(portion_text)

        food = FoodItem(name, "", energy, fats, proteins, carbohydrates, portion, conversions)
        return food

    def __get_div_texts(self, div: Tag) -> List[str]:
        texts = [d.text.strip() for d in div if d.text.strip()]
        texts_filtered = []
        labels = ["Белки", "Жиры", "Углеводы"]

        for i, text in enumerate(texts):
            if i < 7:
                texts_filtered.append(text)
            elif text in labels or texts_filtered[-1] in labels:
                texts_filtered.append(text)

        assert re.fullmatch(r"Размер Порции", texts_filtered[-12])
        assert re.fullmatch(r"\d+ ккал", texts_filtered[-7])
        assert re.fullmatch(r"Жиры", texts_filtered[-6])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-5])
        assert re.fullmatch(r"Углеводы", texts_filtered[-4])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-3])
        assert re.fullmatch(r"Белки", texts_filtered[-2])
        assert re.fullmatch(r"\d+(,\d*)?г", texts_filtered[-1])

        return texts_filtered

    def __get_conversions(self, portion_text: str) -> Dict[PortionUnit, Decimal]:
        conversions = dict()

        match = re.match(r"^1 +(?P<unit>порция|штука|ломтик) +\((?P<value>\d+(.\d*)?) г\)$", portion_text)
        if match:
            unit, value = match.group("unit"), match.group("value")
            conversions[PortionUnit.g] = Decimal("1") / Decimal(value)
            conversions[PortionUnit.from_str(unit)] = Decimal("1")

        match = re.match(r"^1 +(?P<unit>порция|штука|ломтик)$", portion_text)
        if match:
            conversions[PortionUnit.from_str(match.group("unit"))] = Decimal("1")

        return conversions
