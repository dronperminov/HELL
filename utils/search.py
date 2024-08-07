import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

from bson import ObjectId
from fuzzywuzzy import fuzz
from pymongo import MongoClient, ASCENDING
from pymongo.errors import OperationFailure

import constants
from entities.food_item import FoodItem
from entities.meal_item import MealItem
from entities.template import TemplateAvailability
from utils.utils import normalize_statistic, get_current_date


class Search:
    def __init__(self, mongo: MongoClient):
        self.database = mongo[constants.MONGO_DATABASE]
        self.user_collection = self.database[constants.MONGO_USER_COLLECTION]
        self.food_collection = self.database[constants.MONGO_FOOD_COLLECTION]
        self.template_collection = self.database[constants.MONGO_TEMPLATE_COLLECTION]
        self.meal_collection = self.database[constants.MONGO_MEAL_COLLECTION]
        self.diary_collection = self.database[constants.MONGO_DIARY_COLLECTION]

        self.food_collection.create_index([("name", "text"), ("aliases", "text")])
        self.food_collection.create_index([("name", ASCENDING), ("aliases", ASCENDING)])
        self.template_collection.create_index([("name", "text")])
        self.template_collection.create_index([("name", ASCENDING)])

    def search(self, query: str, user_id: str = "") -> List[dict]:
        if not query:
            return []

        try:
            food_items = self.search_food(query)
            food_items.extend(self.search_templates(query, user_id))

            if not re.fullmatch(r"<[^>]+>", query) or query in ["<b>", "<!b>"]:
                self.__sort_food_items(food_items, user_id, query)
            return food_items
        except OperationFailure:
            return []

    def autocomplete(self, query: str, user_id: str) -> List[str]:
        escaped_query = self.__escape_query(query)

        if not escaped_query:
            return []

        results_food = list(self.food_collection.aggregate([
            {"$match": {"$or": [
                {"$text": {"$search": f"{query}", "$caseSensitive": False}},
                {"name": {"$regex": f"{escaped_query}", "$options": "i"}}
            ]}},
            {"$project": {"_id": 1, "name": 1}}
        ]))

        if not user_id:
            return [result["name"] for result in results_food]

        results_template = list(self.template_collection.aggregate([
            {"$match": {"$and": [
                {"$or": [
                    {"$text": {"$search": f"{query}", "$caseSensitive": False}},
                    {"name": {"$regex": f"{escaped_query}", "$options": "i"}}
                ]},
                {"$or": [
                    {"creator_id": ObjectId(user_id)},
                    {"availability": f"{TemplateAvailability.friends}", "creator_id": {"$in": self.__get_template_creators(user_id)}},
                    {"availability": f"{TemplateAvailability.users}"}
                ]}
            ]}},
            {"$project": {"_id": 1, "name": 1, "template": "true"}}
        ]))

        results = results_food + results_template
        self.__sort_food_items(results, user_id, query)
        return [f'<t>:{result["name"]}' if "template" in result else result["name"] for result in results]

    def search_food(self, query: str):
        if query in ["<p>", "<!p>"]:
            food_items = self.__search_food_by_type("proteins", query.startswith("<!"))
        elif query in ["<f>", "<!f>"]:
            food_items = self.__search_food_by_type("fats", query.startswith("<!"))
        elif query in ["<c>", "<!c>"]:
            food_items = self.__search_food_by_type("carbohydrates", query.startswith("<!"))
        elif query == "<b>":
            food_items = list(self.food_collection.find({"aliases": {"$regex": r"^\d+$"}}))
        elif query == "<!b>":
            food_items = list(self.food_collection.find({"aliases": {"$not": {"$regex": r"^\d+$"}}}))
        elif re.fullmatch(r"<[^>]+>", query):
            food_items = list(self.food_collection.find({"name": query[1:-1]}))
        else:
            escaped_query = self.__escape_query(query)
            is_barcode = re.fullmatch(r"\d+", query)

            food_items = list(self.food_collection.find({"$or": [
                {"name": {"$regex": escaped_query, "$options": "i"}},
                {"aliases": {"$elemMatch": {"$regex": f"^{escaped_query}$" if is_barcode else escaped_query, "$options": "i"}}}
            ]}))

            if not food_items:
                food_items = list(self.food_collection.find({"$text": {"$search": query, "$caseSensitive": False}}))

        self.__process_food_items(food_items)
        return food_items

    def search_templates(self, query: str, user_id: str) -> List[dict]:
        if not user_id:
            return []

        if query == "<t>":
            templates = self.__search_user_templates(user_id)
        elif query == "<T>":
            templates = self.__search_available_templates(user_id)
        elif re.fullmatch(r"<[^>]+>", query):
            templates = self.__search_query_templates(f"^{self.__escape_query(query[1:-1])}$", user_id)
        else:
            templates = self.__search_query_templates(self.__escape_query(query), user_id)

        self.__process_templates(templates)
        return templates

    def get_frequent(self, meal_type: str, user_id: str) -> List[dict]:
        pipeline = [{"$match": {"user_id": ObjectId(user_id)}}]

        if meal_type:
            pipeline.append({"$match": {f"meal_info.{meal_type}": {"$exists": True}}})
            pipeline.append({"$project": {f"meal_id": f"$meal_info.{meal_type}", "date": 1, "_id": 0}})
        else:
            pipeline.append({"$project": {"meal_info": {"$objectToArray": "$meal_info"}, "date": 1}})
            pipeline.append({"$unwind": "$meal_info"})
            pipeline.append({"$project": {"meal_id": "$meal_info.v", "date": 1, "_id": 0}})

        pipeline.append({"$unwind": "$meal_id"})

        today = datetime.now()
        documents = list(self.diary_collection.aggregate(pipeline))
        meal_id2date = {document["meal_id"]: document["date"] for document in documents}
        food_items = self.__get_frequent_foods(meal_id2date, today)
        templates = self.__get_frequent_templates(meal_id2date, user_id, today)
        frequent = sorted(food_items + templates, key=lambda v: v["count"], reverse=True)

        return frequent

    def __get_frequent_foods(self, meal_id2date: Dict[ObjectId, datetime], today: datetime) -> List[dict]:
        food2count = defaultdict(int)

        for document in self.meal_collection.find({"_id": {"$in": list(meal_id2date.keys())}, "group_id": {"$exists": False}}):
            food2count[document["food_id"]] += constants.FREQUENT_MEAL_ALPHA ** (today - meal_id2date[document["_id"]]).days
        food2count = {food_id: count for food_id, count in food2count.items()}

        food_items = list(self.food_collection.find({"_id": {"$in": [food_id for food_id in food2count]}}))
        self.__process_food_items(food_items)

        for food_item in food_items:
            food_item["count"] = food2count[food_item["_id"]]

        return food_items

    def __get_frequent_templates(self, meal_id2date: Dict[ObjectId, datetime], user_id: str, today: datetime) -> List[dict]:
        templates2count = defaultdict(set)
        group_id2score = {}

        for document in self.meal_collection.find({"_id": {"$in": list(meal_id2date.keys())}, "group_id": {"$exists": True}}):
            group_id2score[document["group_id"]] = constants.FREQUENT_MEAL_ALPHA ** (today - meal_id2date[document["_id"]]).days
            templates2count[document["group_name"]].add(document["group_id"])

        templates2count = {name: sum(group_id2score[group_id] for group_id in group_ids) for name, group_ids in templates2count.items()}
        template_names = [template_name for template_name in templates2count]

        templates = list(self.template_collection.find({
            "name": {"$in": template_names},
            "$or": [
                {"creator_id": ObjectId(user_id)},
                {"availability": f"{TemplateAvailability.friends}", "creator_id": {"$in": self.__get_template_creators(user_id)}},
                {"availability": f"{TemplateAvailability.users}"}
            ]}
        ))

        self.__process_templates(templates)

        for template in templates:
            template["count"] = templates2count[template["name"]]

        return templates

    def get_recently(self, meal_type: str, user_id: str) -> list:
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id), "date": {"$lte": get_current_date()}}},
            {"$sort": {"date": -1}},
            {"$limit": constants.RECENTLY_MEAL_DAYS_COUNT}
        ]

        if meal_type:
            pipeline.append({"$match": {f"meal_info.{meal_type}": {"$exists": True}}})
            pipeline.append({"$project": {f"meal_id": f"$meal_info.{meal_type}", "date": 1, "_id": 0}})
        else:
            pipeline.append({"$project": {"meal_info": {"$objectToArray": "$meal_info"}, "date": 1}})
            pipeline.append({"$unwind": "$meal_info"})
            pipeline.append({"$project": {"meal_id": "$meal_info.v", "date": 1, "_id": 0}})

        pipeline.append({"$unwind": "$meal_id"})
        pipeline.append({"$sort": {"date": -1, "meal_id": -1}})

        documents = self.diary_collection.aggregate(pipeline)

        meal_ids = [document["meal_id"] for document in documents]
        food_items = self.__get_recently_foods(meal_ids)
        templates = self.__get_recently_template(meal_ids, user_id)

        recent = sorted(food_items + templates, key=lambda v: v["order"])
        return recent

    def __get_recently_foods(self, meal_ids: List[ObjectId]) -> List[dict]:
        documents = self.meal_collection.aggregate([
            {"$match": {"_id": {"$in": meal_ids}, "group_id": {"$exists": False}}},
            {"$addFields": {"order": {"$indexOfArray": [meal_ids, "$_id"]}}},
            {"$group": {"_id": "$food_id", "order": {"$min": "$order"}}},
            {"$sort": {"order": 1}}
        ])

        food2order = {document["_id"]: document["order"] for document in documents}
        food_ids = [food_id for food_id in food2order]

        food_items = list(self.food_collection.find({"_id": {"$in": food_ids}}))
        self.__process_food_items(food_items)

        for food_item in food_items:
            food_item["order"] = food2order[food_item["_id"]]

        return food_items

    def __get_recently_template(self, meal_ids: List[ObjectId], user_id: str) -> List[dict]:
        documents = self.meal_collection.aggregate([
            {"$match": {"_id": {"$in": meal_ids}, "group_id": {"$exists": True}}},
            {"$addFields": {"order": {"$indexOfArray": [meal_ids, "$_id"]}}},
            {"$group": {"_id": "$group_name", "order": {"$min": "$order"}}},
        ])

        templates2order = {document["_id"]: document["order"] for document in documents}
        template_names = [template_name for template_name in templates2order]

        templates = list(self.template_collection.find({
            "name": {"$in": template_names},
            "$or": [
                {"creator_id": ObjectId(user_id)},
                {"availability": f"{TemplateAvailability.friends}", "creator_id": {"$in": self.__get_template_creators(user_id)}},
                {"availability": f"{TemplateAvailability.users}"}
            ]}
        ))

        self.__process_templates(templates)

        for template in templates:
            template["order"] = templates2order[template["name"]]

        return templates

    def __search_food_by_type(self, main_key: str, is_inverse: bool) -> List[dict]:
        other_keys = [key for key in ["proteins", "fats", "carbohydrates"] if key != main_key]
        operator = "$or" if is_inverse else "$and"

        if is_inverse:
            expr = [
                {"$gt": [f"${other_keys[0]}", {"$multiply": [3, f"${main_key}"]}]},
                {"$gt": [f"${other_keys[1]}", {"$multiply": [3, f"${main_key}"]}]}
            ]
        else:
            expr = [
                {"$gt": [f"${main_key}", {"$multiply": [3, f"${other_keys[0]}"]}]},
                {"$gt": [f"${main_key}", {"$multiply": [3, f"${other_keys[1]}"]}]}
            ]

        food_items = list(self.food_collection.aggregate([
            {"$match": {"$expr": {operator: expr}}},
            {"$sort": {main_key: 1 if is_inverse else -1, "name": 1}}
        ]))
        return food_items

    def __search_query_templates(self, query: str, user_id: str) -> List[dict]:
        # TODO: add friends
        templates = list(self.template_collection.find({
            "name": {"$regex": query, "$options": "i"},
            "$or": [
                {"creator_id": ObjectId(user_id)},
                {"availability": f"{TemplateAvailability.friends}", "creator_id": {"$in": self.__get_template_creators(user_id)}},
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
                {"availability": f"{TemplateAvailability.friends}", "creator_id": {"$in": self.__get_template_creators(user_id)}},
                {"availability": f"{TemplateAvailability.users}"}
            ]
        }))

        return templates

    def __escape_query(self, query: str) -> str:
        alternatives = [re.escape(alternative) for alternative in query.split('|') if alternative]
        return "|".join(alternatives)

    def __process_food_items(self, food_items: List[dict]):
        for food_item in food_items:
            normalize_statistic(food_item)

    def __get_template_creators(self, user_id: str) -> List[ObjectId]:
        user_ids = [user["_id"] for user in self.user_collection.find({"friend_users": {"$in": [ObjectId(user_id)]}}, {"_id": 1})]
        return user_ids

    def __process_templates(self, templates: List[dict]):
        user_ids = list({template["creator_id"] for template in templates})
        users = self.user_collection.find({"_id": {"$in": user_ids}}, {"username": 1, "_id": 1})
        users = {user["_id"]: user["username"] for user in users}

        for template in templates:
            self.__process_template(template, users)

    def __process_template(self, template: dict, users: dict) -> dict:
        template["creator_username"] = users[template["creator_id"]]
        template["weight"] = Decimal(str(template.get("weight", "0")))

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

    def __sort_food_items(self, food_items: List[dict], user_id: str, query: str):
        queries = [alternative for alternative in query.lower().split("|") if alternative]
        using_count = self.__get_using_count(user_id)
        food_items.sort(key=lambda food_item: (self.__compare_names(queries, food_item["name"].lower()), -using_count.get(food_item["name"], using_count.get(food_item["_id"], 0))))

    def __get_using_count(self, user_id: str) -> Dict[ObjectId, int]:
        if not user_id:
            return dict()

        meal_ids = [document["meal_id"] for document in self.diary_collection.aggregate([
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$project": {"meal_info": {"$objectToArray": "$meal_info"}}},
            {"$unwind": "$meal_info"},
            {"$project": {"meal_id": "$meal_info.v", "_id": 0}},
            {"$unwind": "$meal_id"}
        ])]

        food_documents = self.meal_collection.aggregate([
            {"$match": {"_id": {"$in": meal_ids}, "group_id": {"$exists": False}}},
            {"$group": {"_id": "$food_id", "count": {"$sum": 1}}},
        ])

        template_documents = self.meal_collection.aggregate([
            {"$match": {"_id": {"$in": meal_ids}, "group_id": {"$exists": True}}},
            {"$group": {"_id": "$group_name", "group_ids": {"$addToSet": "$group_id"}}},
            {"$project": {"_id": 1, "count": {"$size": "$group_ids"}}},
        ])

        using_count = dict()

        for document in food_documents:
            using_count[document["_id"]] = document["count"]

        for document in template_documents:
            using_count[document["_id"]] = document["count"]

        return using_count

    def __compare_names(self, queries: List[str], name: str):
        if not queries:
            return 0

        return -max(fuzz.token_set_ratio(name, query) for query in queries)
