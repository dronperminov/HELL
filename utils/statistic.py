from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from itertools import chain
from typing import List, Dict, Tuple, Iterable

from bson import ObjectId
from pymongo import MongoClient

import constants
from entities.food_item import FoodItem
from entities.meal_item import MealItem
from utils.utils import normalize_statistic, format_date, d2s


class Statistic:
    def __init__(self, mongo: MongoClient):
        self.database = mongo[constants.MONGO_DATABASE]
        self.food_collection = self.database[constants.MONGO_FOOD_COLLECTION]
        self.meal_collection = self.database[constants.MONGO_MEAL_COLLECTION]
        self.diary_collection = self.database[constants.MONGO_DIARY_COLLECTION]

    # TODO: refactor this function
    def get_meals_statistic(self, meal_ids: Iterable[ObjectId], with_food: bool = True) -> dict:
        statistic = {key: Decimal("0") for key in constants.STATISTIC_KEYS}
        foods = []
        last_group = None

        for meal_id in meal_ids:
            meal = MealItem.from_dict(self.meal_collection.find_one({"_id": meal_id}))
            food = self.food_collection.find_one({"_id": ObjectId(meal.food_id)})
            food_item = FoodItem.from_dict(food)
            food_portion = food_item.make_portion(meal.portion_size, meal.portion_unit)

            for key in constants.STATISTIC_KEYS:
                statistic[key] += food_portion[key]

            if with_food:
                food_item_data = {"food_item": food, **food_portion, "meal_id": str(meal_id), "portion_size": d2s(meal.portion_size), "portion_unit": f'{meal.portion_unit}'}

                if not meal.group_id:
                    foods.append(food_item_data)
                    last_group = None
                else:
                    if not last_group or last_group["group_id"] != meal.group_id:
                        last_group = {
                            "name": meal.group_name,
                            "group_id": meal.group_id,
                            "group_portion": meal.group_portion,
                            "foods": [food_item_data],
                            "statistic": {key: Decimal("0") for key in constants.STATISTIC_KEYS}
                        }
                        foods.append(last_group)
                    else:
                        last_group["foods"].append(food_item_data)

                    for key in constants.STATISTIC_KEYS:
                        last_group["statistic"][key] += food_portion[key]

                normalize_statistic(food_item_data)

        normalize_statistic(statistic)

        if with_food:
            for food_item in foods:
                if "group_id" in food_item:
                    normalize_statistic(food_item["statistic"])

            statistic["foods"] = foods

        return statistic

    def get_meal_statistic(self, foods: List[dict]) -> dict:
        statistic = {}

        for food in foods:
            if "group_id" in food:
                statistic[food["group_id"]] = {key: Decimal("0") for key in constants.STATISTIC_KEYS}
                for food_item in food["foods"]:
                    statistic[food_item["meal_id"]] = {key: value for key, value in food_item.items() if key not in ("food_item", "meal_id")}

                    for key in constants.STATISTIC_KEYS:
                        statistic[food["group_id"]][key] += Decimal(food_item[key])

                normalize_statistic(statistic[food["group_id"]])
            else:
                statistic[food["meal_id"]] = {key: value for key, value in food.items() if key not in ("food_item", "meal_id")}

        return statistic

    def prepare_meal_statistic(self, dates_range: List[datetime], date2meal_info_ids: Dict[datetime, dict], meal_types: Dict[str, str]) -> Tuple[Dict[str, dict], Dict[str, dict]]:
        statistic, statistic_meal_type = {}, {}

        for date in dates_range:
            meal_ids = chain.from_iterable(date2meal_info_ids.get(date, {}).values())
            meal_type_ids = date2meal_info_ids.get(date, {})
            date = format_date(date)

            statistic[date] = self.get_meals_statistic(meal_ids, with_food=False)
            statistic_meal_type[date] = {}

            for meal_type in meal_types:
                statistic_meal_type[date][meal_type] = self.get_meals_statistic(meal_type_ids.get(meal_type, []), with_food=False)

        return statistic, statistic_meal_type

    def get_meal_type_count(self, documents: List[dict]):
        meal2count = defaultdict(int)

        for document in documents:
            for meal_type, meal_items in document["meal_info"].items():
                if meal_items:
                    meal2count[meal_type] += 1

        return meal2count

    def get_used_dates(self, user_id: str):
        used_dates = self.diary_collection.aggregate([
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$match": {"$expr": {"$gt": [{"$size": {"$filter": {"input": {"$objectToArray": "$meal_info"}, "as": "pair", "cond": {"$ne": ["$$pair.v", []]}}}}, 0]}}},
            {"$project": {"date": 1, "_id": 0}}
        ])
        return [format_date(date["date"]) for date in used_dates]

    def get_food_item_statistic(self, user_id: str, meal_ids) -> Dict[datetime, dict]:
        statistic = {}

        for document in self.diary_collection.find({"user_id": ObjectId(user_id)}):
            date_statistic = {}

            for meal_type, meals in document.get("meal_info", {}).items():
                meals_statistic = [meal_ids[meal_id] for meal_id in meals if meal_id in meal_ids]

                if meals_statistic:
                    date_statistic[constants.MEAL_TYPE_NAMES.get(meal_type, meal_type)] = meals_statistic

            if date_statistic:
                statistic[document["date"]] = date_statistic

        return statistic
