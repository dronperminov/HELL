from typing import Optional, List, Dict, Tuple

import requests
from bs4 import BeautifulSoup, Tag
import re
from decimal import Decimal

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

        title = soup.find("title")
        name = title.text.replace(" Калории и Пищевая Ценность", "")
        energy = Decimal(texts[-7].split(' ')[0])
        fats = Decimal(texts[-5][:-1].replace(',', '.'))
        carbohydrates = Decimal(texts[-3][:-1].replace(',', '.'))
        proteins = Decimal(texts[-1][:-1].replace(',', '.'))

        try:
            portion, conversions, scale = self.__get_portion_info(texts[-11].replace(",", "."))
            food = FoodItem(name, "", energy * scale, fats * scale, proteins * scale, carbohydrates * scale, portion, conversions)
            return food
        except ValueError:
            return None

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

    def __get_portion_info(self, portion_text: str) -> Tuple[BasePortionUnit, Dict[PortionUnit, Decimal], Decimal]:
        conversions = dict()

        if portion_text in [BasePortionUnit.g100, BasePortionUnit.ml100]:
            return BasePortionUnit(portion_text), conversions, Decimal("1")

        match = re.match(r"^1 +(?P<unit>порция|шт|ломтик)(ука)? +\((?P<value>\d+(.\d*)?) г\)$", portion_text)
        if match:
            unit, value = match.group("unit"), match.group("value")
            scale = Decimal("100") / Decimal(value)
            conversions[PortionUnit(unit)] = Decimal(value) / Decimal("100")
            return BasePortionUnit.g100, conversions, scale

        raise ValueError(f'Invalid portion description: "{portion_text}"')
