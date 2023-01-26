import re
from decimal import Decimal
from typing import List, Mapping, Any, Dict

from pymongo.errors import OperationFailure

from entities.food_item import FoodItem
from entities.meal_item import MealItem
from entities.template import TemplateAvailability
from bson import ObjectId
from pymongo import MongoClient

import constants
from utils import normalize_statistic


class Search:
    def __init__(self, mongo: MongoClient):
        self.database = mongo[constants.MONGO_DATABASE]
        self.user_collection = self.database[constants.MONGO_USER_COLLECTION]
        self.food_collection = self.database[constants.MONGO_FOOD_COLLECTION]
        self.template_collection = self.database[constants.MONGO_TEMPLATE_COLLECTION]
        self.meal_collection = self.database[constants.MONGO_MEAL_COLLECTION]

    def search(self, query: str, user_id: str = "") -> List[dict]:
        if not query:
            return []

        try:
            food_items = self.search_food(query)
            food_items.extend(self.search_templates(query, user_id))
            self.__sort_food_items(food_items, user_id)
            return food_items
        except OperationFailure:
            return []

    def search_food(self, query: str):
        if query == "<F>":
            food_items = list(self.food_collection.find({}))
        else:
            food_items = list(self.food_collection.find({"$or": [
                {"name": {"$regex": re.escape(query), "$options": "i"}},
                {"aliases": {"$elemMatch": {"$regex": re.escape(query), "$options": "i"}}}
            ]}))

        self.__process_food_items(food_items)
        return food_items

    def search_templates(self, query: str, user_id: str) -> List[dict]:
        if not user_id:
            return []

        if query == "<t>":
            templates = self.__search_user_templates(user_id)
        elif query == "<T>":
            templates = self.__search_available_templates(user_id)
        else:
            query = re.escape(query)
            templates = self.__search_query_templates(query, user_id)

        self.__process_templates(templates)
        return templates

    def get_frequent_foods(self, meal_type: str, user_id: str) -> list:
        pipeline = []

        if meal_type in constants.MEAL_TYPES:
            pipeline.append({"$match": {f"meal_info.{meal_type}": {"$exists": True}}})
            pipeline.append({"$project": {f"meal_id": f"$meal_info.{meal_type}", "_id": 0}})
        else:
            pipeline.append({"$project": {"meal_info": {"$objectToArray": "$meal_info"}}})
            pipeline.append({"$unwind": "$meal_info"})
            pipeline.append({"$project": {"meal_id": "$meal_info.v", "_id": 0}})

        pipeline.append({"$unwind": "$meal_id"})

        diary_collection = self.database[constants.MONGO_DIARY_COLLECTION + user_id]
        documents = diary_collection.aggregate(pipeline)

        meal_ids = [document["meal_id"] for document in documents]
        documents = self.meal_collection.aggregate([
            {"$match": {"_id": {"$in": meal_ids}}},
            {"$group": {"_id": "$food_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": constants.FREQUENT_MEAL_MIN_COUNT}}},
            {"$sort": {"count": -1}},
            {"$limit": constants.FREQUENT_MEAL_CLIP_COUNT}
        ])

        food_ids = [document["_id"] for document in documents]
        food_items = list(self.food_collection.aggregate([
            {"$match": {"_id": {"$in": food_ids}}},
            {"$addFields": {"order": {"$indexOfArray": [food_ids, "$_id"]}}},
            {"$sort": {"order": 1}}
        ]))

        self.__process_food_items(food_items)
        self.__sort_food_items(food_items, user_id)
        return food_items

    def __search_query_templates(self, query: str, user_id: str) -> List[dict]:
        # TODO: add friends
        templates = list(self.template_collection.find({
            "name": {"$regex": query, "$options": "i"},
            "$or": [
                {"creator_id": ObjectId(user_id)},
                {"availability": f"{TemplateAvailability.users}"}
            ]
        }))

        return templates

    def __search_user_templates(self, user_id: str) -> List[dict]:
        templates = list(self.template_collection.find({"creator_id": ObjectId(user_id)}))
        return templates

    def __search_available_templates(self, user_id: str) -> List[dict]:
        templates = list(self.template_collection.find({
            "$or": [
                {"creator_id": ObjectId(user_id)},
                {"availability": f"{TemplateAvailability.users}"}
            ]
        }))

        return templates

    def __process_food_items(self, food_items: List[dict]):
        for food_item in food_items:
            normalize_statistic(food_item)

    def __process_templates(self, templates: List[dict]):
        user_ids = list({template["creator_id"] for template in templates})
        users = self.user_collection.find({"_id": {"$in": user_ids}}, {"username": 1, "_id": 1})
        users = {user["_id"]: user["username"] for user in users}

        for template in templates:
            self.__process_template(template, users)

    def __process_template(self, template: dict, users: dict) -> dict:
        template["creator_username"] = users[template["creator_id"]]

        for key in constants.STATISTIC_KEYS:
            template[key] = Decimal("0")

        for meal_item in template["meal_items"]:
            meal = MealItem.from_dict(meal_item)
            food = self.food_collection.find_one({"_id": ObjectId(meal.food_id)})
            food_item = FoodItem.from_dict(food)
            food_portion = food_item.make_portion(meal.portion_size, meal.portion_unit)

            for key in constants.STATISTIC_KEYS:
                template[key] += food_portion[key]

        return normalize_statistic(template)

    def __sort_food_items(self, food_items: List[dict], user_id: str):
        food2count = self.__get_using_count(user_id)
        food_items.sort(key=lambda food_item: (-self.__get_food_item_count(food_item, food2count), food_item["name"]))

    def __get_using_count(self, user_id: str) -> Dict[ObjectId, int]:
        if not user_id:
            return dict()

        diary_collection = self.database[constants.MONGO_DIARY_COLLECTION + user_id]
        documents = diary_collection.aggregate([
            {"$project": {"meal_info": {"$objectToArray": "$meal_info"}}},
            {"$unwind": "$meal_info"},
            {"$project": {"meal_id": "$meal_info.v", "_id": 0}},
            {"$unwind": "$meal_id"}
        ])

        meal_ids = [document["meal_id"] for document in documents]
        documents = self.meal_collection.aggregate([
            {"$match": {"_id": {"$in": meal_ids}}},
            {"$group": {"_id": "$food_id", "count": {"$sum": 1}}},
        ])

        food2count = {document["_id"]: document["count"] for document in documents}
        return food2count

    def __get_food_item_count(self, food_item: dict, food2count: Dict[ObjectId, int]) -> float:
        if "creator_id" not in food_item:
            return food2count.get(food_item["_id"], 0)

        meal_items = food_item["meal_items"]
        return sum(food2count.get(meal_item["food_id"], 0) for meal_item in meal_items) / len(meal_items)
