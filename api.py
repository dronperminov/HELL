from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain
from typing import Optional, List, Dict

import jwt
from bson import Decimal128
from bson.objectid import ObjectId
from fastapi import FastAPI, Query, Request, Response, Depends, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient
from pymongo.errors import OperationFailure

import constants
from auth_utils import validate_password, create_access_token, JWT_SECRET_KEY, ALGORITHM, COOKIE_NAME
from entities.food_item import FoodItem
from entities.meal_item import MealItem
from fatsecret_parser import FatSecretParser
from utils import d2s, get_current_date, get_dates_range, format_date, parse_date, parse_period, add_default_unit

app = FastAPI()
app.mount("/styles", StaticFiles(directory="web/styles"))
app.mount("/js", StaticFiles(directory="web/js"))
app.mount("/images", StaticFiles(directory="web/images"))
app.mount("/fonts", StaticFiles(directory="web/fonts"))
templates = Environment(loader=FileSystemLoader('web/templates'), cache_size=0)

mongo = MongoClient(constants.MONGO_URL)
database = mongo[constants.MONGO_DATABASE]


async def token_to_user_id(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/login", scheme_name="JWT"))) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])

        if datetime.fromtimestamp(payload["exp"]) < datetime.now():
            return None
    except:
        return None

    user_collection = database[constants.MONGO_USER_COLLECTION]
    user = user_collection.find_one({"username": payload["sub"]})

    if user is None:
        return None

    return str(user["_id"])


async def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get(COOKIE_NAME)
    return await token_to_user_id(token)


def unauthorized_access(url: str) -> Response:
    # template = templates.get_template('not_authorized.html')
    # return HTMLResponse(content=template.render(url=url))
    return RedirectResponse("/login", status_code=302)


@app.get("/")
async def index(user_id: Optional[str] = Depends(get_current_user)):
    if user_id:
        user_collection = database[constants.MONGO_USER_COLLECTION]
        user = user_collection.find_one({"_id": ObjectId(user_id)})
    else:
        user = None

    template = templates.get_template('index.html')
    return HTMLResponse(content=template.render(user=user, page="/"))


@app.get("/login")
def login_get(user_id: Optional[str] = Depends(get_current_user)):
    if user_id:
        return RedirectResponse(url="/", status_code=302)

    template = templates.get_template('login.html')
    return HTMLResponse(content=template.render())


@app.post('/login')
def login(username: str = Form(...), password: str = Form(...)):
    user_collection = database[constants.MONGO_USER_COLLECTION]
    user = user_collection.find_one({"username": username.lower()})

    if user is None:
        return JSONResponse({"status": "fail", "message": f"Пользователь \"{username}\" не существует"})

    if not validate_password(password, user['password_hash']):
        return JSONResponse({"status": "fail", "message": "Имя пользователя или пароль введены неверно"})

    access_token = create_access_token(user["username"])
    response = JSONResponse(content={"status": "ok"})
    response.set_cookie(key="Authorization", value=access_token, httponly=True)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


def get_food_by_query(query: Optional[str]) -> list:
    if not query:
        return []

    try:
        food_collection = database[constants.MONGO_FOOD_COLLECTION]
        return list(food_collection.find({"name": {"$regex": query, "$options": "i"}}))
    except OperationFailure:
        return []


def get_frequent_foods(meal_type: str, user_id: str) -> list:
    pipeline = []

    if meal_type in constants.MEAL_TYPES:
        pipeline.append({"$match": {f"meal_info.{meal_type}": {"$exists": True}}})
        pipeline.append({"$project": {f"meal_id": f"$meal_info.{meal_type}", "_id": 0}})
    else:
        pipeline.append({"$project": {"meal_info": {"$objectToArray": "$meal_info"}}})
        pipeline.append({"$unwind": "$meal_info"})
        pipeline.append({"$project": {"meal_id": "$meal_info.v", "_id": 0}})

    pipeline.append({"$unwind": "$meal_id"})

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    documents = diary_collection.aggregate(pipeline)

    meal_ids = [document["meal_id"] for document in documents]
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    documents = meal_collection.aggregate([
        {"$match": {"_id": {"$in": meal_ids}}},
        {"$group": {"_id": "$food_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": constants.FREQUENT_MEAL_MIN_COUNT}}},
        {"$sort": {"count": -1}}
    ])

    food_ids = [document["_id"] for document in documents]
    food_collection = database[constants.MONGO_FOOD_COLLECTION]
    food_items = food_collection.aggregate([
        {"$match": {"_id": {"$in": food_ids}}},
        {"$addFields": {"order": {"$indexOfArray": [food_ids, "$_id"]}}},
        {"$sort": {"order": 1}}
    ])

    return list(food_items)


@app.get("/food-collection")
def food_collection_get(food_query: str = Query(None)):
    if food_query is not None and not food_query:
        return RedirectResponse(url="/food-collection", status_code=302)

    food_items = get_food_by_query(food_query)
    template = templates.get_template('food_collection.html')
    html = template.render(food_items=food_items, query=food_query, page="/food-collection")
    return HTMLResponse(content=html)


@app.get("/add-food")
def add_food_get(food_query: str = Query(None), date: str = Query(None), meal_type: str = Query(None)):
    template = templates.get_template('food_form.html')
    html = template.render(
        title="Добавление нового продукта",
        add_text="Добавить продукт",
        add_url="/add-food",
        page="/add-food",
        query=food_query,
        date=date,
        meal_type=meal_type)
    return HTMLResponse(content=html)


@app.post("/add-food")
async def add_food_post(request: Request):
    try:
        data = await request.json()
        food = FoodItem.from_dict(data)
        food_collection = database[constants.MONGO_FOOD_COLLECTION]

        if list(food_collection.find({"name": food.name})):
            return JSONResponse({"status": "FAIL", "message": f"Не удалось добавить, так как продукт с названием \"{food.name}\" уже существует"})

        food_collection.insert_one(food.to_dict())
        href = "food-collection" if "date" not in data else f"add-meal/{data['date']}/{data['meal_type']}"
        return JSONResponse({"status": "OK", "href": f"/{href}?food_query={food.name[:25]}", "message": "Продукт успешно добавлен"})
    except Exception as e:
        return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить продукт из-за ошибки: {e}"})


@app.get("/edit-food/{food_id}")
def edit_food(food_id: str, food_query: str = Query(None)):
    food_collection = database[constants.MONGO_FOOD_COLLECTION]
    food = food_collection.find_one({"_id": ObjectId(food_id)})
    template = templates.get_template('food_form.html')
    html = template.render(title="Редактирование продукта", add_text="Обновить продукт", add_url=f"/edit-food/{food_id}", food=food, page="/edit-food", query=food_query)
    return HTMLResponse(content=html)


@app.post("/edit-food/{food_id}")
async def edit_food_post(food_id: str, request: Request):
    try:
        food_collection = database[constants.MONGO_FOOD_COLLECTION]

        data = await request.json()
        original_food = food_collection.find_one({"_id": ObjectId(food_id)})
        edited_food = FoodItem.from_dict(data)

        if original_food["name"] != edited_food.name and list(food_collection.find({"name": edited_food.name})):
            return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить, так как продукт с названием \"{edited_food.name}\" уже существует"})

        food_collection.update_one({"_id": ObjectId(food_id)}, {"$set": edited_food.to_dict()})
        return JSONResponse({"status": "OK", "href": f"/food-collection?food_query={edited_food.name[:25]}", "message": "Продукт успешно обновлён"})
    except Exception as e:
        return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить продукт из-за ошибки: {e}"})


@app.post("/remove-food")
def remove_food(food_id: str = Body(..., embed=True)):
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal = meal_collection.find_one({"food_id": ObjectId(food_id)})

    if meal:
        return JSONResponse({"status": "fail", "message": "Невозможно удалить этот продукт, так как он используется в дневнике"})

    food_collection = database[constants.MONGO_FOOD_COLLECTION]
    food_collection.delete_one({"_id": ObjectId(food_id)})
    return JSONResponse({"status": "ok"})


def get_meal_info(date: datetime, user_id: str) -> Dict[str, List[ObjectId]]:
    meal_info = OrderedDict()

    for meal_type in constants.MEAL_TYPES:
        meal_info[meal_type] = []

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    meal_doc = diary_collection.find_one({"date": date})

    if meal_doc:
        for meal_type, meal_ids in meal_doc["meal_info"].items():
            meal_info[meal_type] = meal_ids

    return meal_info


def get_meal_statistic(meal_ids: List[ObjectId], with_food: bool = True) -> dict:
    foods = []
    statistics = {
        "energy": Decimal("0"),
        "fats": Decimal("0"),
        "proteins": Decimal("0"),
        "carbohydrates": Decimal("0"),
    }

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    food_collection = database[constants.MONGO_FOOD_COLLECTION]

    for meal_id in meal_ids:
        meal = MealItem.from_dict(meal_collection.find_one({"_id": meal_id}))
        food = food_collection.find_one({"_id": ObjectId(meal.food_id)})
        food_item = FoodItem.from_dict(food)
        food_portion = food_item.make_portion(meal.portion_size, meal.portion_unit)

        for key, value in food_portion.items():
            statistics[key] += value
            food_portion[key] = d2s(value)

        if with_food:
            foods.append({"food_item": food, **food_portion, "meal_id": str(meal_id), "portion_size": d2s(meal.portion_size), "portion_unit": f'{meal.portion_unit}'})

    for key, value in statistics.items():
        statistics[key] = d2s(value)

    if with_food:
        statistics["foods"] = foods

    return statistics


@app.get("/diary")
def diary(date: Optional[str] = Query(None), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/diary")

    date = parse_date(date) if date else get_current_date()
    meal_info = get_meal_info(date, user_id)
    meal_statistic = {meal_type: get_meal_statistic(meal_ids) for meal_type, meal_ids in meal_info.items()}

    template = templates.get_template('diary.html')
    content = template.render(
        date=format_date(date),
        prev_date=format_date(date + timedelta(days=-1)),
        next_date=format_date(date + timedelta(days=1)),
        meal_info=meal_info,
        names=constants.MEAL_TYPES_RUS,
        meal_statistic=meal_statistic,
        page="/diary"
    )

    return HTMLResponse(content=content)


@app.get("/add-meal/{date}/{meal_type}")
def add_meal_get(date: str, meal_type: str, food_query: str = Query(None), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/diary")

    food_items = get_food_by_query(food_query)
    frequent_food_items = get_frequent_foods(meal_type, user_id) if not food_query else []

    template = templates.get_template('food_collection.html')
    html = template.render(
        food_items=add_default_unit(food_items),
        frequent_food_items=add_default_unit(frequent_food_items),
        query=food_query,
        date=date,
        meal_type=meal_type,
        names=constants.MEAL_TYPES_RUS,
        page="/add-meal"
    )
    return HTMLResponse(content=html)


@app.post("/add-meal")
def add_meal(
        date: str = Body(..., embed=True),
        meal_type: str = Body(..., embed=True),
        food_id: str = Body(..., embed=True),
        portion_size: str = Body(..., embed=True),
        portion_unit: str = Body(..., embed=True),
        user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]

    meal = meal_collection.insert_one({"food_id": ObjectId(food_id), "portion_size": portion_size, "portion_unit": portion_unit})
    diary_collection.update_one({"date": date}, {"$push": {f"meal_info.{meal_type}": meal.inserted_id}}, upsert=True)

    return JSONResponse({"status": "ok"})


@app.post("/remove-meal")
def remove_meal(date: str = Body(..., embed=True), meal_type: str = Body(..., embed=True), meal_id: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal_collection.delete_one({"_id": ObjectId(meal_id)})

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    diary_collection.update_one({"date": date}, {"$pull": {f"meal_info.{meal_type}": ObjectId(meal_id)}})
    meal_ids = diary_collection.find_one({"date": date}).get("meal_info", {}).get(meal_type, [])
    statistic = get_meal_statistic(meal_ids)
    meal_statistic = {food["meal_id"]: {key: value for key, value in food.items() if key not in ("food_item", "meal_id")} for food in statistic.pop("foods")}
    return JSONResponse({"status": "ok", "statistic": statistic, "meal_statistic": meal_statistic})


@app.post("/edit-meal")
def edit_meal(
        date: str = Body(..., embed=True),
        meal_type: str = Body(..., embed=True),
        meal_id: str = Body(..., embed=True),
        portion_size: str = Body(..., embed=True),
        portion_unit: str = Body(..., embed=True),
        user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal_collection.update_one({"_id": ObjectId(meal_id)}, {"$set": {"portion_size": Decimal128(portion_size), "portion_unit": portion_unit}})

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    meal_ids = diary_collection.find_one({"date": date}).get("meal_info", {}).get(meal_type, [])
    statistic = get_meal_statistic(meal_ids)
    meal_statistic = {food["meal_id"]: {key: value for key, value in food.items() if key not in ("food_item", "meal_id")} for food in statistic.pop("foods")}

    return JSONResponse({"status": "ok", "statistic": statistic, "meal_statistic": meal_statistic})


@app.post("/add-meal-type")
def add_meal_type(date: str = Body(..., embed=True), meal_type: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    diary_collection.update_one({"date": date}, {"$set": {f"meal_info.{meal_type}": []}})
    return JSONResponse({"status": "ok"})


@app.post("/remove-meal-type")
def remove_meal_type(date: str = Body(..., embed=True), meal_type: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]

    meal_doc = diary_collection.find_one({"date": date})
    meal_ids = meal_doc["meal_info"][meal_type]

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal_collection.delete_many({"_id": {"$in": meal_ids}})
    diary_collection.update_one({"date": date}, {"$unset": {f"meal_info.{meal_type}": 1}})

    return JSONResponse({"status": "ok"})


@app.post("/parse-fatsecret")
async def parse_fatsecret(request: Request):
    data = await request.json()
    parser = FatSecretParser()

    if "query" in data:
        return JSONResponse(parser.parse_search(data["query"]))

    food = parser.parse(data["url"].replace("https://", "http://"))

    if food:
        return JSONResponse(food.to_json())

    return JSONResponse(None)


@app.get("/statistic")
def get_statistic(period: str = Query(None), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/statistic")

    start_date, end_date, period = parse_period(period)

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    documents = diary_collection.find({"date": {"$gte": start_date, "$lte": end_date}})
    date2meal_ids = {document["date"]: chain.from_iterable(meal_ids for meal_ids in document["meal_info"].values()) for document in documents}

    dates_range = get_dates_range(start_date, end_date)
    statistic = {format_date(date): get_meal_statistic(date2meal_ids.get(date, []), with_food=False) for date in dates_range}

    template = templates.get_template("statistic.html")
    content = template.render(
        start_date=format_date(start_date),
        end_date=format_date(end_date),
        period=period,
        statistic=statistic,
        dates_range=[format_date(date) for date in dates_range]
    )

    return HTMLResponse(content=content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
