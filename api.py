import config
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient


app = FastAPI()
app.mount("/styles", StaticFiles(directory="web/styles"))
templates = Environment(loader=FileSystemLoader('web/templates'), cache_size=0)

mongo = MongoClient(config.MONGO_URL)
database = mongo[config.MONGO_DATABASE]


@app.get("/food-collection")
def food_collection(food_query: str = Query(None)):
    if food_query is not None and not food_query:
        return RedirectResponse(url="/food-collection", status_code=302)

    food_collection = database[config.MONGO_FOOD_COLLECTION]

    if food_query:
        food_items = food_collection.find({"name": {"$regex": food_query, "$options": "i"}}, {"_id": 0})
    else:
        food_items = food_collection.find({}, {"_id": 0})

    template = templates.get_template('food_collection.html')
    html = template.render(food_items=list(food_items), query=food_query)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
