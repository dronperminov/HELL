import json
import decimal

from entities.food_item import FoodItem


class FoodItemEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)

        if isinstance(obj, FoodItem):
            return obj.__dict__

        return json.JSONEncoder.default(self, obj)


class FoodCollection:
    def __init__(self, path: str):
        self.foods = dict()
        self.path = path

    def add(self, food_item: FoodItem) -> bool:
        food_id = food_item.id

        if food_id in self.foods:
            return False

        self.foods[food_id] = food_item
        return True

    def print(self):
        print("-----------------------------------------------------")
        print(f" FOOD COLLECTION ({len(self.foods)})                  ")
        print("-----------------------------------------------------")

        for food_item in self.foods.values():
            print(food_item)
            print("-----------------------------------------------------")

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.foods, f, cls=FoodItemEncoder, ensure_ascii=False, indent=2)

    def load(self):
        self.foods = dict()

        with open(self.path, encoding="utf-8") as f:
            foods = json.load(f)

        for food_id, food_item_data in foods.items():
            self.foods[food_id] = FoodItem.from_dict(food_item_data)
