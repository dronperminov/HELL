import config
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient
from bson.objectid import ObjectId

from entities.food_item import FoodItem
from fatsecret_parser import FatSecretParser


app = FastAPI()
app.mount("/styles", StaticFiles(directory="web/styles"))
app.mount("/js", StaticFiles(directory="web/js"))
templates = Environment(loader=FileSystemLoader('web/templates'), cache_size=0)

mongo = MongoClient(config.MONGO_URL)
database = mongo[config.MONGO_DATABASE]


@app.get("/food-collection")
def food_collection_get(food_query: str = Query(None)):
    if food_query is not None and not food_query:
        return RedirectResponse(url="/food-collection", status_code=302)

    food_collection = database[config.MONGO_FOOD_COLLECTION]

    if food_query:
        food_items = food_collection.find({"name": {"$regex": food_query, "$options": "i"}})
    else:
        food_items = food_collection.find({})

    template = templates.get_template('food_collection.html')
    html = template.render(food_items=list(food_items), query=food_query, click_url="/edit-food")
    return HTMLResponse(content=html)


@app.get("/add-food")
def add_food_get():
    template = templates.get_template('food_form.html')
    html = template.render(title="Добавление нового продукта", add_text="Добавить продукт", add_url="/add-food")
    return HTMLResponse(content=html)


@app.post("/add-food")
async def add_food_post(request: Request):
    try:
        data = await request.json()
        food = FoodItem.from_dict(data)
        food_collection = database[config.MONGO_FOOD_COLLECTION]

        if list(food_collection.find({"name": food.name})):
            return JSONResponse({"status": "FAIL", "message": f"Не удалось добавить, так как продукт с названием \"{food.name}\" уже существует"})

        food_collection.insert_one(food.to_dict())
        return JSONResponse({"status": "OK", "href": f"/food-collection?food_query={food.name[:25]}", "message": "Продукт успешно добавлен"})
    except Exception as e:
        return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить продукт из-за ошибки: {e}"})


@app.get("/edit-food/{food_id}")
def edit_food(food_id: str):
    food_collection = database[config.MONGO_FOOD_COLLECTION]
    food = food_collection.find_one({"_id": ObjectId(food_id)})
    template = templates.get_template('food_form.html')
    html = template.render(title="Редактирование продукта", add_text="Обновить продукт", add_url=f"/edit-food/{food_id}", food=food)
    return HTMLResponse(content=html)


@app.post("/edit-food/{food_id}")
async def edit_food_post(food_id: str, request: Request):
    try:
        food_collection = database[config.MONGO_FOOD_COLLECTION]

        data = await request.json()
        original_food = food_collection.find_one({"_id": ObjectId(food_id)})
        edited_food = FoodItem.from_dict(data)

        if original_food["name"] != edited_food.name and list(food_collection.find({"name": edited_food.name})):
            return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить, так как продукт с названием \"{edited_food.name}\" уже существует"})

        food_collection.update_one({"_id": ObjectId(food_id)}, {"$set": edited_food.to_dict()})
        return JSONResponse({"status": "OK", "href": f"/food-collection", "message": "Продукт успешно обновлён"})
    except Exception as e:
        return JSONResponse({"status": "FAIL", "message": f"Не удалось обновить продукт из-за ошибки: {e}"})


@app.post("/parse-fatsecret")
async def parse_fatsecret(request: Request):
    data = await request.json()
    parser = FatSecretParser()
    food = parser.parse(data["url"].replace("https://", "http://"))

    if food:
        return JSONResponse(food.to_json())

    return JSONResponse(None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
