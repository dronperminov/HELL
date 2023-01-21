from typing import Optional, Dict
from decimal import Decimal
from bson.decimal128 import Decimal128
from dataclasses import dataclass

from entities.portion_unit import BasePortionUnit, PortionUnit


@dataclass
class FoodItem:
    food_id: str
    name: str
    description: str
    energy: Decimal
    fats: Decimal
    proteins: Decimal
    carbohydrates: Decimal
    portion: BasePortionUnit
    conversions: Optional[Dict[PortionUnit, Decimal]] = None

    def __post_init__(self) -> None:
        if self.portion == BasePortionUnit.g100:
            self.conversions[PortionUnit.g] = Decimal("0.01")
        elif self.portion == BasePortionUnit.ml100:
            self.conversions[PortionUnit.ml] = Decimal("0.01")
            self.conversions[PortionUnit.tea_spoon] = Decimal("0.05")
            self.conversions[PortionUnit.table_spoon] = Decimal("0.18")

    def make_portion(self, portion_size: Decimal, portion_unit: PortionUnit) -> dict:
        scale = self.conversions[portion_unit] * portion_size
        return {
            "energy": self.energy * scale,
            "fats": self.fats * scale,
            "proteins": self.proteins * scale,
            "carbohydrates": self.carbohydrates * scale
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FoodItem":
        food_id = str(data.get("_id", ""))
        name = data["name"]
        description = data["description"]
        energy = Decimal(str(data["energy"]))
        fats = Decimal(str(data["fats"]))
        proteins = Decimal(str(data["proteins"]))
        carbohydrates = Decimal(str(data["carbohydrates"]))

        portion = BasePortionUnit(data["portion"])
        conversions = {PortionUnit(unit): Decimal(str(value)) for unit, value in data["conversions"].items()}

        return cls(food_id, name, description, energy, fats, proteins, carbohydrates, portion, conversions)

    def to_dict(self) -> dict:
        return dict(
            name=self.name,
            description=self.description,
            portion=self.portion,
            conversions={PortionUnit(unit): Decimal128(str(value)) for unit, value in self.conversions.items()},
            energy=Decimal128(str(self.energy)),
            fats=Decimal128(str(self.fats)),
            proteins=Decimal128(str(self.proteins)),
            carbohydrates=Decimal128(str(self.carbohydrates))
        )

    def to_json(self) -> dict:
        return {
            "id": self.food_id,
            "name": self.name,
            "description": self.description,
            "portion": self.portion,
            "conversions": {PortionUnit(unit): float(str(value)) for unit, value in self.conversions.items()},
            "energy": float(str(self.energy)),
            "fats": float(str(self.fats)),
            "proteins": float(str(self.proteins)),
            "carbohydrates": float(str(self.carbohydrates))
        }

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
