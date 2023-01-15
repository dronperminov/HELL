MONGO_URL = "mongodb://localhost:27017/"
MONGO_DATABASE = "hell"

MONGO_FOOD_COLLECTION = "food_collection"
MONGO_USER_COLLECTION = "users"
MONGO_MEAL_COLLECTION = "meal_collection"
MONGO_DIARY_COLLECTION = "diary"

DATE_FORMAT = "%d.%m.%Y"

BREAKFAST = "breakfast"
LUNCH = "lunch"
DINNER = "dinner"
MEAL_TYPES = [BREAKFAST, LUNCH, DINNER]

MEAL_TYPES_RUS = {
    BREAKFAST: "Завтрак",
    LUNCH: "Обед",
    DINNER: "Ужин"
}

FREQUENT_MEAL_MIN_COUNT = 2