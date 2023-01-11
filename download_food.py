import config
from pymongo import MongoClient
from fatsecret_parser import FatSecretParser


def main():
    mongo = MongoClient(config.MONGO_URL)
    db = mongo[config.MONGO_DATABASE]

    food_collection = db[config.MONGO_FOOD_COLLECTION]
    food_collection.drop()

    parser = FatSecretParser()

    with open("data/fatsecret_urls.txt", encoding="utf-8") as f:
        urls = f.read().splitlines()

    for url in urls:
        if not url or url.startswith("#"):
            continue

        food = parser.parse(f"http://www.fatsecret.ru/калории-питание/{url}")

        if not food:
            print("Couldn't download", url)
        else:
            food_collection.insert_one(food.to_dict())
            print("Added", url)


if __name__ == '__main__':
    main()
