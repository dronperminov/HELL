from fatsecret_parser import FatSecretParser
from db_collections.food_collection import FoodCollection


def main():
    parser = FatSecretParser()
    food_collection = FoodCollection(path="data/food_collection.json")

    with open("data/fatsecret_urls.txt", encoding="utf-8") as f:
        urls = f.read().splitlines()

    for url in urls:
        if not url or url.startswith("#"):
            continue

        food = parser.parse(f"http://www.fatsecret.ru/калории-питание/{url}")

        if not food:
            print("Couldn't download", url)
        else:
            food_collection.add(food)
            print("Added", url)

    food_collection.save()
    food_collection.load()
    food_collection.print()


if __name__ == '__main__':
    main()
