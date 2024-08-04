MONGO_URL = "mongodb://localhost:27017/"
MONGO_DATABASE = "hell"

MONGO_FOOD_COLLECTION = "food_collection"
MONGO_USER_COLLECTION = "users"
MONGO_USER_PARAMETERS = "user_parameters"
MONGO_SETTINGS_COLLECTION = "settings_collection"
MONGO_MEAL_COLLECTION = "meal_collection"
MONGO_TEMPLATE_COLLECTION = "template_collection"
MONGO_DIARY_COLLECTION = "diary"

DATE_FORMAT = "%d.%m.%Y"

BREAKFAST = "breakfast"
LUNCH = "lunch"
DINNER = "dinner"
OTHER = "other"
MEAL_TYPES = [BREAKFAST, LUNCH, DINNER]

MEAL_TYPE_NAMES = {
    BREAKFAST: "Завтрак",
    LUNCH: "Обед",
    DINNER: "Ужин",
    OTHER: "Прочее"
}

FREQUENT_MEAL_ALPHA = 0.97
FREQUENT_MEAL_CLIP_COUNT = 15
RECENTLY_MEAL_DAYS_COUNT = 14
RECENTLY_MEAL_CLIP_COUNT = 25
STATISTIC_MEAL_TYPE_MIN_COUNT = 3

STATISTIC_KEYS = ["proteins", "fats", "carbohydrates", "energy"]

SLICE_NAMES = ["ломтик"]
PORTION_NAMES = ["порция", "мерных скупа", "чашка"]

EVERYDAY = "everyday"
WEEKDAYS = "weekdays"
WEEKENDS = "weekends"
