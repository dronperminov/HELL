from enum import Enum


class MealType(str, Enum):
    breakfast = "Завтрак"
    dinner = "Обед"
    supper = "Ужин"
    other = "Прочее"
