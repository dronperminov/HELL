import re
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain
from typing import Optional, List, Dict, Tuple, Iterable

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
from auth_utils import validate_password, get_password_hash, create_access_token, JWT_SECRET_KEY, ALGORITHM, COOKIE_NAME, LOCAL_STORAGE_COOKIE_NAME
from entities.food_item import FoodItem
from entities.meal_item import MealItem
from entities.template import Template, TemplateAvailability
from entities.user_settings import UserSettings
from fatsecret_parser import FatSecretParser
from utils import d2s, normalize_statistic, get_current_date, get_dates_range, format_date, parse_date, parse_period, add_default_unit
from search import Search

app = FastAPI()
app.mount("/styles", StaticFiles(directory="web/styles"))
app.mount("/js", StaticFiles(directory="web/js"))
app.mount("/images", StaticFiles(directory="web/images"))
app.mount("/fonts", StaticFiles(directory="web/fonts"))
templates = Environment(loader=FileSystemLoader('web/templates'), cache_size=0)

mongo = MongoClient(constants.MONGO_URL)
database = mongo[constants.MONGO_DATABASE]
search = Search(mongo)
database[constants.MONGO_SETTINGS_COLLECTION].create_index([("user_id", 1)])


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
    if token is None:
        token = request.cookies.get(LOCAL_STORAGE_COOKIE_NAME)

    return await token_to_user_id(token)


def unauthorized_access(url: str) -> Response:
    # template = templates.get_template('not_authorized.html')
    # return HTMLResponse(content=template.render(url=url))
    return RedirectResponse("/login", status_code=302)


def get_user_settings(user_id: str) -> UserSettings:
    settings_collection = database[constants.MONGO_SETTINGS_COLLECTION]
    settings_data = settings_collection.find_one({"user_id": ObjectId(user_id)})

    if settings_data is None:
        settings_data = {"user_id": user_id}

    return UserSettings.from_dict(settings_data)


def error_page(error_text: str, user_id: str) -> Response:
    template = templates.get_template('error.html')
    return HTMLResponse(template.render(error_text=error_text, user_id=user_id))


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
    response = JSONResponse(content={"status": "ok", "token": access_token})
    response.set_cookie(key="Authorization", value=access_token, httponly=True)
    return response


@app.get("/settings")
def settings_get(user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    template = templates.get_template('settings.html')
    content = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id)
    )
    return HTMLResponse(content=content)


@app.post("/settings")
async def settings_post(request: Request, user_id: Optional[str] = Depends(get_current_user)):
    data = await request.json()
    settings = UserSettings.from_dict(data)
    settings_collection = database[constants.MONGO_SETTINGS_COLLECTION]
    settings_collection.update_one({"user_id": ObjectId(user_id)}, {"$set": settings.to_dict()}, upsert=True)
    return JSONResponse({"status": "ok"})


@app.get("/update-password")
def update_password_get(user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    template = templates.get_template('update_password.html')
    content = template.render(user_id=user_id, settings=get_user_settings(user_id))
    return HTMLResponse(content=content)


@app.post("/update-password")
def update_password(
        old_password: str = Body(..., embed=True),
        password: str = Body(..., embed=True),
        password_confirm: str = Body(..., embed=True),
        user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь"})

    user_collection = database[constants.MONGO_USER_COLLECTION]
    user = user_collection.find_one({"_id": ObjectId(user_id)})

    if not validate_password(old_password, user['password_hash']):
        return JSONResponse({"status": "fail", "message": "Старый пароль введён неверно"})

    if old_password == password:
        return JSONResponse({"status": "fail", "message": "Новый пароль совпадает со старым"})

    if password != password_confirm:
        return JSONResponse({"status": "fail", "message": "Подтверждение пароля не совпадает"})

    if len(password) < 8:
        return JSONResponse({"status": "fail", "message": "Пароль должен состоять как мимимум из 8 символов"})

    user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": get_password_hash(password)}})
    access_token = create_access_token(user["username"])
    response = JSONResponse(content={"status": "ok", "token": access_token})
    response.set_cookie(key="Authorization", value=access_token, httponly=True)
    return response


@app.get("/logout")
def logout(return_page: str = Query("/")):
    response = RedirectResponse(return_page, status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


def have_body_parameter(user_id: str, name: str) -> bool:
    user_collection = database[constants.MONGO_USER_COLLECTION]
    return user_collection.find_one({"_id": ObjectId(user_id), "body_parameters.name": name}) is not None


def get_body_parameters(user_id: str, date: datetime) -> Tuple[List[datetime], Dict[str, int], List[dict]]:
    parameters_collection = database[constants.MONGO_USER_PARAMETERS + user_id]
    parameter_docs = parameters_collection.aggregate([
        {"$group": {"_id": "$name", "values": {"$addToSet": {"value": "$value", "date": "$date"}}}}
    ])

    used_dates = [used_date["_id"] for used_date in parameters_collection.aggregate([{"$group": {"_id": "$date"}}])]
    parameters = {}
    body_date_indices = {}

    for parameter_doc in parameter_docs:
        parameter_name: str = parameter_doc["_id"]
        values = [{"date": format_date(parameter["date"]), "value": d2s(Decimal(str(parameter["value"])))} for parameter in parameter_doc["values"]]
        parameters[parameter_name] = sorted(values, key=lambda value_item: parse_date(value_item["date"]))
        body_date_indices[parameter_name] = -1

        for i, parameter in enumerate(parameters[parameter_name]):
            if parse_date(parameter["date"]) <= date:
                body_date_indices[parameter_name] = i

    return used_dates, body_date_indices, parameters


@app.get("/")
async def index(date: Optional[str] = Query(None), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        template = templates.get_template('index.html')
        return HTMLResponse(content=template.render(page="/"))

    date = parse_date(date) if date else get_current_date()

    user_collection = database[constants.MONGO_USER_COLLECTION]
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    body_used_dates, body_date_indices, body_parameters = get_body_parameters(user_id, date)

    template = templates.get_template('index.html')
    content = template.render(
        user=user,
        settings=get_user_settings(user_id),
        date=format_date(date),
        prev_date=format_date(date + timedelta(days=-1)),
        next_date=format_date(date + timedelta(days=1)),
        body_used_dates=[format_date(used_date) for used_date in body_used_dates],
        body_date_indices=body_date_indices,
        body_parameters=body_parameters,
        page="/"
    )

    return HTMLResponse(content=content)


@app.post("/add-body-parameter")
def add_body_parameter(date: str = Body(..., embed=True), name: str = Body(..., embed=True), value: str = Body(..., embed=True), unit: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    if have_body_parameter(user_id, name):
        return JSONResponse({"status": "fail", "message": f"Не удалось добавить параметр \"{name}\", так как он уже есть. Пожалуйста, обновите страницу."})

    date = parse_date(date)
    value = Decimal128(value)

    user_collection = database[constants.MONGO_USER_COLLECTION]
    user_collection.update_one({"_id": ObjectId(user_id)}, {"$push": {"body_parameters": {"name": name, "unit": unit}}}, upsert=True)

    parameters_collection = database[constants.MONGO_USER_PARAMETERS + user_id]
    parameters_collection.insert_one({"date": date, "name": name, "value": value})

    return JSONResponse({"status": "ok"})


@app.post("/remove-body-parameter")
def remove_body_parameter(name: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    if not have_body_parameter(user_id, name):
        return JSONResponse({"status": "fail", "message": f"Не удалось удалить параметр \"{name}\", так как его нет среди параметров. Пожалуйста, обновите страницу."})

    user_collection = database[constants.MONGO_USER_COLLECTION]
    user_collection.update_one({"_id": ObjectId(user_id)}, {"$pull": {"body_parameters": {"name": name}}})

    parameters_collection = database[constants.MONGO_USER_PARAMETERS + user_id]
    parameters_collection.delete_many({"name": name})

    return JSONResponse({"status": "ok"})


@app.post("/update-body-parameter-value")
def update_body_parameter_value(date: str = Body(..., embed=True), name: str = Body(..., embed=True), value: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    if not have_body_parameter(user_id, name):
        return JSONResponse({"status": "fail", "message": f"Не удалось обновить параметр \"{name}\", так как его нет среди параметров"})

    date = parse_date(date)
    value = Decimal128(value)

    parameters_collection = database[constants.MONGO_USER_PARAMETERS + user_id]
    parameters_collection.update_one({"date": date, "name": name}, {"$set": {"value": value}}, upsert=True)

    return JSONResponse({"status": "ok"})


@app.post("/remove-body-parameter-value")
def remove_body_parameter_value(date: str = Body(..., embed=True), name: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    if not have_body_parameter(user_id, name):
        return JSONResponse({"status": "fail", "message": f"Не удалось удалить значение параметра \"{name}\", так как его нет среди параметров"})

    date = parse_date(date)

    parameters_collection = database[constants.MONGO_USER_PARAMETERS + user_id]
    parameters_collection.delete_one({"date": date, "name": name})

    return JSONResponse({"status": "ok"})


@app.get("/food-collection")
def food_collection_get(food_query: str = Query(None), user_id: str = Depends(get_current_user)):
    if food_query is not None and not food_query:
        return RedirectResponse(url="/food-collection", status_code=302)

    food_query = food_query.strip() if food_query else None
    food_items = search.search(food_query, user_id)
    template = templates.get_template('food_collection.html')
    content = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        food_items=food_items,
        query=food_query,
        page="/food-collection"
    )
    return HTMLResponse(content=content)


@app.post("/food-collection")
def food_collection_post(food_query: str = Body(..., embed=True)):
    food_query = food_query.strip() if food_query else None
    food_items = search.search(food_query)
    food_items = [FoodItem.from_dict(food_item).to_json() for food_item in food_items]
    food_items = add_default_unit(food_items)
    return JSONResponse(food_items)


@app.get("/autocomplete")
def autocomplete(food_query: str = Query(""), user_id: str = Depends(get_current_user)):
    names = search.autocomplete(food_query, user_id)
    return JSONResponse({"names": names})


@app.get("/add-food")
def add_food_get(food_query: str = Query(None), date: str = Query(None), meal_type: str = Query(None), user_id: str = Depends(get_current_user)):
    template = templates.get_template('food_form.html')
    html = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
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
    data = await request.json()
    food = FoodItem.from_dict(data)
    food_collection = database[constants.MONGO_FOOD_COLLECTION]

    if food_collection.find_one({"name": food.name}):
        return JSONResponse({"status": "FAIL", "message": f"Не удалось добавить, так как продукт с названием \"{food.name}\" уже существует"})

    food_collection.insert_one(food.to_dict())
    href = "food-collection" if "date" not in data else f"add-meal/{data['date']}/{data['meal_type']}"
    return JSONResponse({"status": "ok", "href": f"/{href}?food_query={food.name[:25]}", "message": "Продукт успешно добавлен"})


@app.get("/edit-food/{food_id}")
def edit_food(food_id: str, food_query: str = Query(None), back_url: str = Query(None), user_id: str = Depends(get_current_user)):
    food_collection = database[constants.MONGO_FOOD_COLLECTION]
    food = food_collection.find_one({"_id": ObjectId(food_id)})

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    used_units = [unit["_id"] for unit in meal_collection.aggregate([
        {"$match": {"food_id": ObjectId(food_id)}},
        {"$group": {"_id": "$portion_unit"}}
    ])]

    template = templates.get_template('food_form.html')
    html = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        title="Редактирование продукта",
        add_text="Обновить продукт",
        add_url=f"/edit-food/{food_id}",
        food=normalize_statistic(food),
        used_units=used_units,
        page="/edit-food",
        query=food_query,
        back_url=back_url
    )
    return HTMLResponse(content=html)


@app.post("/edit-food/{food_id}")
async def edit_food_post(food_id: str, request: Request, back_url: str = Query(None)):
    food_collection = database[constants.MONGO_FOOD_COLLECTION]

    data = await request.json()
    original_food = food_collection.find_one({"_id": ObjectId(food_id)})
    edited_food = FoodItem.from_dict(data)

    if original_food["name"] != edited_food.name and list(food_collection.find({"name": edited_food.name})):
        return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить, так как продукт с названием \"{edited_food.name}\" уже существует"})

    food_collection.update_one({"_id": ObjectId(food_id)}, {"$set": edited_food.to_dict()})
    href = back_url if back_url else f"/food-collection?food_query={edited_food.name[:25]}"
    return JSONResponse({"status": "ok", "href": href, "message": "Продукт успешно обновлён"})


@app.post("/remove-food")
def remove_food(food_id: str = Body(..., embed=True)):
    food_id = ObjectId(food_id)
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal = meal_collection.find_one({"food_id": food_id})

    if meal:
        return JSONResponse({"status": "fail", "message": "Невозможно удалить этот продукт, так как он используется в дневнике"})

    template_collection = database[constants.MONGO_TEMPLATE_COLLECTION]
    template = template_collection.find_one({"meal_items": {"$elemMatch": {"food_id": food_id }}})

    if template:
        return JSONResponse({"status": "fail", "message": f'Невозможно удалить этот продукт, так как он используется в шаблоне "{template["name"]}"'})

    food_collection = database[constants.MONGO_FOOD_COLLECTION]
    food_collection.delete_one({"_id": food_id})
    return JSONResponse({"status": "ok"})


def get_editable_template(template: Template, template_id: str = ""):
    food_ids = template.get_food_ids()
    food_id_positions = {food_id: i for i, food_id in enumerate(food_ids)}
    food_collection = database[constants.MONGO_FOOD_COLLECTION]
    food_items = list(food_collection.find({"_id": {"$in": food_ids}}))
    food_items = sorted(food_items, key=lambda food_item: food_id_positions[food_item["_id"]])
    meal_info = template.get_meal_info()
    meal_items = []

    for food_item in food_items:
        meal_items.append({
            "portion_size": d2s(meal_info[food_item["_id"]].portion_size),
            "portion_unit": f'{meal_info[food_item["_id"]].portion_unit}',
            "name": food_item["name"],
            "description": food_item["description"],
            "id": str(food_item["_id"]),
            "conversions": {f'{unit}': d2s(value, 100) for unit, value in food_item["conversions"].items()},
            **{key: d2s(value) for key, value in food_item.items() if key in constants.STATISTIC_KEYS}
        })

    template_data = {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "availability": f"{template.availability}",
        "meal_items": meal_items,
        "creator_id": template.creator_id
    }

    return template_data


@app.get("/add-template")
def add_template_get(food_query: str = Query(None), date: str = Query(None), meal_type: str = Query(None), user_id: str = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    template = templates.get_template('template_form.html')
    html = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        title="Добавление нового шаблона",
        add_text="Добавить шаблон",
        add_url="/add-template",
        page="/add-template",
        query=food_query,
        date=date,
        meal_type=meal_type)
    return HTMLResponse(content=html)


@app.get("/create-template")
def create_template(date: str = Query(None), meal_type: str = Query(None), user_id: str = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    diary_doc = diary_collection.find_one({"date": parse_date(date)})

    if not diary_doc:
        return error_page(f"Не удалось создать шаблон, так как в дневнике нет записей за {date}", user_id)

    meal_ids = diary_doc["meal_info"].get(meal_type, [])

    if len(meal_ids) == 0:
        return error_page(f"Не удалось создать шаблон, так как в дневнике за {date} нет записей на этот приём пищи", user_id)

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meals = [MealItem.from_dict(meal_item) for meal_item in meal_collection.find({"_id": {"$in": meal_ids}})]

    template = Template("", "", meals, TemplateAvailability.me, str(user_id))
    template_data = get_editable_template(template)

    template = templates.get_template('template_form.html')
    html = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        title="Добавление нового шаблона",
        add_text="Добавить шаблон",
        add_url="/add-template",
        page="/add-template",
        query="",
        template=template_data
    )
    return HTMLResponse(content=html)


@app.post("/add-template")
async def add_template_post(request: Request, user_id: str = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Не удалось добавить шаблон, так как Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    data = await request.json()
    template = Template.from_dict(data)

    template_collection = database[constants.MONGO_TEMPLATE_COLLECTION]
    if template_collection.find_one({"name": template.name, "creator_id": ObjectId(user_id)}):
        return JSONResponse({"status": "FAIL", "message": f"Не удалось добавить, так как шаблон с названием \"{template.name}\" уже существует"})

    food_ids = [ObjectId(meal_item.food_id) for meal_item in template.meal_items]
    food_collection = database[constants.MONGO_FOOD_COLLECTION]

    if len(list(food_collection.find({"_id": {"$in": food_ids}}))) != len(food_ids):
        return JSONResponse({"status": "fail", "message": "Не удалось добавить шаблон, так как некоторых продуктов больше не существует"})

    template_collection.insert_one(template.to_dict())

    href = "food-collection" if "date" not in data else f"add-meal/{data['date']}/{data['meal_type']}"
    return JSONResponse({"status": "ok", "href": f"/{href}?food_query={template.name[:25]}", "message": "Шаблон успешно добавлен"})


@app.get("/edit-template/{template_id}")
def edit_template(template_id: str, food_query: str = Query(None), back_url: str = Query(None), user_id: str = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/")

    template_collection = database[constants.MONGO_TEMPLATE_COLLECTION]
    template = template_collection.find_one({"_id": ObjectId(template_id)})

    if not template:
        return error_page("Этот шаблон больше не существует", user_id)

    template = Template.from_dict(template)
    template_data = get_editable_template(template, template_id)

    if template.availability == TemplateAvailability.me and template.creator_id != user_id:
        return error_page("Этот шаблон недоступен для редактирования по решению автора", user_id)

    template = templates.get_template('template_form.html')
    html = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        title="Редактирование шаблона",
        add_text="Обновить шаблон",
        add_url=f"/edit-template/{template_id}",
        template=template_data,
        page="/edit-template",
        query=food_query,
        back_url=back_url
    )
    return HTMLResponse(content=html)


@app.post("/edit-template/{template_id}")
async def edit_template_post(template_id: str, request: Request, back_url: str = Query(None), user_id: str = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Не удалось обновить шаблон, так как Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    try:
        template_collection = database[constants.MONGO_TEMPLATE_COLLECTION]
        original_template = template_collection.find_one({"_id": ObjectId(template_id)})

        if not original_template:
            return JSONResponse({"status": "fail", "message": "Не удалось обновить шаблон, так как его больше не существует"})

        original_template = Template.from_dict(original_template)
        data = await request.json()
        edited_template = Template.from_dict(data)

        if original_template.availability == TemplateAvailability.me and edited_template.creator_id != user_id:
            return JSONResponse({"status": "fail", "message": "Этот шаблон недоступен для редактирования по решению автора"})

        if original_template.name != edited_template.name and list(template_collection.find({"name": edited_template.name, "creator_id": edited_template.creator_id})):
            return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить, так как шаблон с названием \"{edited_template.name}\" уже существует"})

        template_collection.update_one({"_id": ObjectId(template_id)}, {"$set": edited_template.to_dict()})
        href = back_url if back_url else f"/food-collection?food_query={edited_template.name[:25]}"
        return JSONResponse({"status": "ok", "href": href, "message": "Шаблон успешно обновлён"})
    except ConnectionError as e:
        return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить шаблон из-за ошибки: {e}"})


@app.post("/remove-template")
def remove_template(template_id: str = Body(..., embed=True), user_id: str = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Не удалось обновить шаблон, так как Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    template_collection = database[constants.MONGO_TEMPLATE_COLLECTION]
    template = template_collection.find_one({"_id": ObjectId(template_id)})

    if not template:
        return JSONResponse({"status": "fail", "message": "Не удалось удалить шаблон, так как его больше не существует"})

    if str(template["creator_id"]) != user_id:
        return JSONResponse({"status": "fail", "message": "Удалить шаблон может только его создатель"})

    result = template_collection.delete_one({"_id": ObjectId(template_id)})

    if result.deleted_count != 1:
        return JSONResponse({"status": "fail", "message": "Не удалось удалить шаблон, так как он уже удалён"})

    return JSONResponse({"status": "ok"})


def get_meal_info(date: datetime, user_id: str, settings: UserSettings) -> Tuple[Dict[str, List[ObjectId]], Optional[Dict[str, Decimal128]]]:
    meal_info = OrderedDict()

    for meal_type in constants.MEAL_TYPES:
        meal_info[meal_type] = []

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    meal_doc = diary_collection.find_one({"date": date})
    limits = {}

    if meal_doc:
        limits = meal_doc.get("limits", {})
        for meal_type, meal_ids in meal_doc["meal_info"].items():
            meal_info[meal_type] = meal_ids

    if date >= get_current_date() and not limits and settings.limits and settings.add_limits:
        limits = settings.limits_to_dict()
        data = {"limits": limits}

        if not meal_doc:
            data["meal_info"] = meal_info

        diary_collection.update_one({"date": date}, {"$set": data}, upsert=True)

    return meal_info, limits


# TODO: refactor this function
def get_meals_statistic(meal_ids: Iterable[ObjectId], with_food: bool = True) -> dict:
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    food_collection = database[constants.MONGO_FOOD_COLLECTION]

    statistic = {key: Decimal("0") for key in constants.STATISTIC_KEYS}
    foods = []
    last_group = None

    for meal_id in meal_ids:
        meal = MealItem.from_dict(meal_collection.find_one({"_id": meal_id}))
        food = food_collection.find_one({"_id": ObjectId(meal.food_id)})
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
                    last_group = {"name": meal.group_name, "group_id": meal.group_id, "foods": [food_item_data], "statistic": {key: Decimal("0") for key in constants.STATISTIC_KEYS}}
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


def get_meal_statistic(foods: List[dict]) -> dict:
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


def prepare_meal_statistic(dates_range: List[datetime], date2meal_info_ids: Dict[datetime, dict], meal_types: Dict[str, str]) -> Tuple[Dict[str, dict], Dict[str, dict]]:
    statistic, statistic_meal_type = {}, {}

    for date in dates_range:
        meal_ids = chain.from_iterable(date2meal_info_ids.get(date, {}).values())
        meal_type_ids = date2meal_info_ids.get(date, {})
        date = format_date(date)

        statistic[date] = get_meals_statistic(meal_ids, with_food=False)
        statistic_meal_type[date] = {}

        for meal_type in meal_types:
            statistic_meal_type[date][meal_type] = get_meals_statistic(meal_type_ids.get(meal_type, []), with_food=False)

    return statistic, statistic_meal_type


def get_meal_type_count(documents: List[dict]):
    meal2count = defaultdict(int)

    for document in documents:
        for meal_type in document["meal_info"]:
            meal2count[meal_type] += 1

    return meal2count


def get_used_dates(user_id: str):
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    used_dates = diary_collection.aggregate([
        {"$match": {"$expr": {"$gt": [{"$size": {"$filter": {"input": {"$objectToArray": "$meal_info"}, "as": "pair", "cond": {"$ne": ["$$pair.v", []]}}}}, 0]}}},
        {"$project": {"date": 1, "_id": 0}}
    ])
    return [format_date(date["date"]) for date in used_dates]


@app.get("/diary")
def diary(date: Optional[str] = Query(None), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/diary")

    curr_date = get_current_date()
    date = parse_date(date) if date else curr_date
    settings = get_user_settings(user_id)
    copy_date = curr_date + timedelta(days=(1 if date == curr_date else 0))
    meal_info, limits = get_meal_info(date, user_id, settings)
    meal_statistic = {meal_type: get_meals_statistic(meal_ids) for meal_type, meal_ids in meal_info.items()}

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    documents = diary_collection.find({}, {"meal_info": 1})
    meal2count = get_meal_type_count(documents)
    meal_names = [meal_type for meal_type, count in meal2count.items() if count >= constants.STATISTIC_MEAL_TYPE_MIN_COUNT and meal_type not in meal_statistic]

    template = templates.get_template('diary.html')
    content = template.render(
        user_id=user_id,
        settings=settings,
        date=format_date(date),
        used_dates=get_used_dates(user_id),
        copy_date=format_date(copy_date),
        meal_info=meal_info,
        names=constants.MEAL_TYPE_NAMES,
        limits=limits,
        meal_statistic=meal_statistic,
        meal_names=meal_names,
        page="/diary"
    )

    return HTMLResponse(content=content)


@app.post("/save-limits")
def save_limits(date: str = Body(..., embed=True), limits: dict = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    limits = {name: Decimal128(value) for name, value in limits.items()}

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    result = diary_collection.update_one({"date": date}, {"$set": {"limits": limits}}, upsert=True)

    if result.matched_count != 1:
        result = diary_collection.update_one({"date": date}, {"$set": {"meal_info": {meal_type: [] for meal_type in constants.MEAL_TYPES}}})

    if result.modified_count != 1 and result.matched_count != 1:
        return JSONResponse({"status": "fail", "message": "Не удалось обновить информацию о лимитах"})

    return JSONResponse({"status": "ok"})


@app.get("/add-meal/{date}/{meal_type}")
def add_meal_get(date: str, meal_type: str, food_query: str = Query(None), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return unauthorized_access("/diary")

    food_query = food_query.strip() if food_query else None
    food_items = search.search(food_query, user_id)
    frequent_food_items = search.get_frequent_foods(meal_type, user_id) if not food_query else []

    template = templates.get_template('food_collection.html')
    html = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        food_items=add_default_unit(food_items),
        frequent_food_items=add_default_unit(frequent_food_items),
        query=food_query,
        date=date,
        meal_type=meal_type,
        names=constants.MEAL_TYPE_NAMES,
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
        return JSONResponse({"status": "fail", "message": "Не удалось добавить продукт, так как Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal = meal_collection.insert_one({"food_id": ObjectId(food_id), "portion_size": Decimal128(portion_size), "portion_unit": portion_unit})

    if not meal:
        return JSONResponse({"status": "fail", "message": "Не удалось добавить продукт, так как его больше не существует"})

    date = parse_date(date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    diary_collection.update_one({"date": date}, {"$push": {f"meal_info.{meal_type}": meal.inserted_id}}, upsert=True)

    return JSONResponse({"status": "ok"})


@app.post("/add-meal-template")
def add_meal_template(
        date: str = Body(..., embed=True),
        meal_type: str = Body(..., embed=True),
        template_id: str = Body(..., embed=True),
        portion_size: str = Body(..., embed=True),
        user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Не удалось добавить шаблон, так как Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    template_collection = database[constants.MONGO_TEMPLATE_COLLECTION]
    template = template_collection.find_one({"_id": ObjectId(template_id)})

    if not template:
        return JSONResponse({"status": "fail", "message": "Не удалось добавить шаблон, так как его больше не существует"})

    date = parse_date(date)
    meal_items = template["meal_items"]
    group_id = ObjectId()

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]

    for meal_item in meal_items:
        meal_portion_size = Decimal(str(meal_item["portion_size"])) * Decimal(portion_size)
        meal = meal_collection.insert_one({
            "food_id": meal_item["food_id"],
            "portion_size": Decimal128(str(meal_portion_size)),
            "portion_unit": meal_item["portion_unit"],
            "group_name": template["name"],
            "group_id": group_id
        })

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
    statistic = get_meals_statistic(meal_ids)
    meal_statistic = get_meal_statistic(statistic.pop("foods"))
    return JSONResponse({"status": "ok", "statistic": statistic, "meal_statistic": meal_statistic})


@app.post("/remove-meal-group")
def remove_meal_group(date: str = Body(..., embed=True), meal_type: str = Body(..., embed=True), group_id: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal_ids = [doc["_id"] for doc in meal_collection.find({"group_id": ObjectId(group_id)}, {"_id": 1})]
    meal_collection.delete_many({"group_id": ObjectId(group_id)})

    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    diary_collection.update_many({"date": date}, {"$pull": {f"meal_info.{meal_type}": {"$in": meal_ids}}})

    meal_ids = diary_collection.find_one({"date": date}).get("meal_info", {}).get(meal_type, [])
    statistic = get_meals_statistic(meal_ids)
    meal_statistic = get_meal_statistic(statistic.pop("foods"))
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
    statistic = get_meals_statistic(meal_ids)
    meal_statistic = get_meal_statistic(statistic.pop("foods"))

    return JSONResponse({"status": "ok", "statistic": statistic, "meal_statistic": meal_statistic})


@app.post("/add-meal-type")
def add_meal_type(date: str = Body(..., embed=True), meal_type: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]

    meal_doc = diary_collection.find_one({"date": date})

    if meal_doc and meal_type in meal_doc["meal_info"]:
        return JSONResponse({"status": "fail", "message": "Невозможно добавить приём пищи, так как он уже существует"})

    diary_collection.update_one({"date": date}, {"$set": {f"meal_info.{meal_type}": []}}, upsert=True)
    return JSONResponse({"status": "ok"})


@app.post("/remove-meal-type")
def remove_meal_type(date: str = Body(..., embed=True), meal_type: str = Body(..., embed=True), user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]

    meal_doc = diary_collection.find_one({"date": date})

    if not meal_doc or meal_type not in meal_doc["meal_info"]:
        return JSONResponse({"status": "fail", "message": "Невозможно удалить приём пищи, так как он уже удалён"})

    meal_ids = meal_doc["meal_info"][meal_type]

    meal_collection = database[constants.MONGO_MEAL_COLLECTION]
    meal_collection.delete_many({"_id": {"$in": meal_ids}})
    diary_collection.update_one({"date": date}, {"$unset": {f"meal_info.{meal_type}": 1}})

    return JSONResponse({"status": "ok"})


@app.post("/rename-meal-type")
def remove_meal_type(
        date: str = Body(..., embed=True),
        meal_type: str = Body(..., embed=True),
        new_meal_type: str = Body(..., embed=True),
        user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]

    meal_doc = diary_collection.find_one({"date": date})

    if not meal_doc or meal_type not in meal_doc["meal_info"]:
        return JSONResponse({"status": "fail", "message": "Невозможно переименовать приём пищи, так как его больше не существует"})

    if meal_type != new_meal_type and new_meal_type in meal_doc["meal_info"]:
        return JSONResponse({"status": "fail", "message": "Невозможно переименовать приём пищи, так как выбранное название уже присутствует"})

    if meal_type != new_meal_type:
        diary_collection.update_one({"date": date}, {"$rename": {f"meal_info.{meal_type}": f"meal_info.{new_meal_type}"}})

    return JSONResponse({"status": "ok"})


@app.post("/copy-meal-type")
def copy_meal_type(
        date: str = Body(..., embed=True),
        meal_type: str = Body(..., embed=True),
        paste_date: str = Body(..., embed=True),
        paste_meal_type: str = Body(..., embed=True),
        user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        return JSONResponse({"status": "fail", "message": "Вы не авторизованы. Пожалуйста, авторизуйтесь."})

    date = parse_date(date)
    paste_date = parse_date(paste_date)
    diary_collection = database[constants.MONGO_DIARY_COLLECTION + user_id]
    meal_collection = database[constants.MONGO_MEAL_COLLECTION]

    meal_doc = diary_collection.find_one({"date": date})
    meal_ids = meal_doc["meal_info"][meal_type]

    meals = list(meal_collection.find({"_id": {"$in": meal_ids}}, {"_id": 0}))
    group_ids = dict()

    for meal_item in meals:
        if "group_id" not in meal_item:
            continue

        group_id = meal_item["group_id"]
        if group_id not in group_ids:
            group_ids[group_id] = ObjectId()
        meal_item["group_id"] = group_ids[group_id]

    inserted_meals = meal_collection.insert_many(meals)

    for meal_id in inserted_meals.inserted_ids:
        diary_collection.update_one({"date": paste_date}, {"$push": {f"meal_info.{paste_meal_type}": meal_id}}, upsert=True)
    return JSONResponse({"status": "ok"})


@app.post("/parse-fatsecret")
async def parse_fatsecret(request: Request):
    data = await request.json()
    parser = FatSecretParser()

    if "query" in data:
        return JSONResponse(parser.parse_search(data["query"], data.get("page", 0)))

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
    documents = list(diary_collection.find({"date": {"$gte": start_date, "$lte": end_date}}))
    total_meal2count = get_meal_type_count(diary_collection.find({}, {"meal_info": 1}))
    meal2count = get_meal_type_count(documents)
    meal_types = OrderedDict()
    for meal_type in constants.MEAL_TYPES:
        if meal_type in meal2count:
            meal_types[meal_type] = constants.MEAL_TYPE_NAMES[meal_type]

    date2meal_info_ids = {}

    for document in documents:
        date2meal_info_ids[document["date"]] = defaultdict(list)

        for meal_type, meal_ids in document["meal_info"].items():
            meal_type_key = meal_type if total_meal2count[meal_type] >= constants.STATISTIC_MEAL_TYPE_MIN_COUNT or meal_type in constants.MEAL_TYPES else constants.OTHER
            date2meal_info_ids[document["date"]][meal_type_key].extend(meal_ids)
            meal_types[meal_type_key] = constants.MEAL_TYPE_NAMES.get(meal_type_key, meal_type_key)

    dates_range = get_dates_range(start_date, end_date)
    statistic, statistic_meal_type = prepare_meal_statistic(dates_range, date2meal_info_ids, meal_types)

    template = templates.get_template("statistic.html")
    content = template.render(
        user_id=user_id,
        settings=get_user_settings(user_id),
        start_date=format_date(start_date),
        end_date=format_date(end_date),
        period=period,
        statistic=statistic,
        used_dates=get_used_dates(user_id),
        statistic_meal_type=statistic_meal_type,
        meal_types=meal_types,
        dates_range=[format_date(date) for date in dates_range],
        page="/statistic"
    )

    return HTMLResponse(content=content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
