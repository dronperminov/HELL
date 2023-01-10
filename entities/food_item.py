from typing import Optional, Dict
from decimal import Decimal
from bson.decimal128 import Decimal128

from entities.portion_unit import BasePortionUnit, PortionUnit


class FoodItem:
    def __init__(self, name: str, description: str,
                 energy: Decimal, fats: Decimal, proteins: Decimal, carbohydrates: Decimal,
                 portion: BasePortionUnit, conversions: Optional[Dict[PortionUnit, Decimal]] = None):
        self.name = name
        self.description = description
        self.portion = portion
        self.conversions = conversions if conversions else dict()
        self.energy = energy
        self.fats = fats
        self.proteins = proteins
        self.carbohydrates = carbohydrates

        self.__init_base_conversions()

    def add_conversion(self, unit: PortionUnit, value: Decimal) -> None:
        if unit in self.conversions:
            raise ValueError(f"Unit {unit} already include")

        self.conversions[unit] = value

    def __init_base_conversions(self) -> None:
        if self.portion == BasePortionUnit.g100:
            self.conversions[PortionUnit.g] = Decimal("0.01")
        elif self.portion == BasePortionUnit.ml100:
            self.conversions[PortionUnit.ml] = Decimal("0.01")
            self.conversions[PortionUnit.tea_spoon] = Decimal("0.05")
            self.conversions[PortionUnit.table_spoon] = Decimal("0.18")

    @staticmethod
    def from_dict(data: dict) -> "FoodItem":
        name = data["name"]
        description = data["description"]
        energy = Decimal(str(data["energy"]))
        fats = Decimal(str(data["fats"]))
        proteins = Decimal(str(data["proteins"]))
        carbohydrates = Decimal(str(data["carbohydrates"]))

        portion = BasePortionUnit.from_str(data["portion"])
        conversions = {PortionUnit.from_str(unit): Decimal(str(value)) for unit, value in data["conversions"].items()}

        food_item = FoodItem(name, description, energy, fats, proteins, carbohydrates, portion, conversions)
        return food_item

    def to_dict(self) -> dict:
        return dict(
            name=self.name,
            description=self.description,
            portion=self.portion,
            conversions={PortionUnit.from_str(unit): Decimal128(str(value)) for unit, value in self.conversions.items()},
            energy=Decimal128(str(self.energy)),
            fats=Decimal128(str(self.fats)),
            proteins=Decimal128(str(self.proteins)),
            carbohydrates=Decimal128(str(self.carbohydrates))
        )

    def __repr__(self) -> str:
        lines = [
            f"Наименование: {self.name}",
            f"Описание: {self.description if self.description else '-'}",
            f"Порция: {self.portion}, (варианты: {', '.join(unit + '->' + str(value) for unit, value in self.conversions.items())})",
            f"Энергетическая ценность: {self.energy} ккал",
            f"Жиры: {self.fats}г",
            f"Белки: {self.proteins}г",
            f"Углеводы: {self.carbohydrates}г"
        ]

        return "\n".join(lines)
