from decimal import Decimal
from entities.portion_unit import PortionUnit


class MealItem:
    def __init__(self, food_id: str, portion_size: Decimal, portion_unit: PortionUnit):
        self.food_id = food_id
        self.portion_size = portion_size
        self.portion_unit = portion_unit
