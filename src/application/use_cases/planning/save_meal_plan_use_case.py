import uuid
from datetime import date, datetime
from typing import List

from src.domain.models.daily_meal_plan import DailyMealPlan
from src.domain.models.recipe import Recipe
from src.shared.exceptions.custom import InvalidRequestDataException

class SaveMealPlanUseCase:
    def __init__(self, meal_plan_repository, recipe_repository):
        self.meal_plan_repository = meal_plan_repository
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str, plan_date: date, meals: List[dict]) -> DailyMealPlan:
        existing_plan = self.meal_plan_repository.find_by_user_and_date(user_uid, plan_date)
        if existing_plan:
            raise InvalidRequestDataException("Ya existe un plan de comidas para ese día.")

        # Verificar duplicados en categorías
        categories_seen = set()
        for meal in meals:
            category = meal["category"]
            if category in categories_seen:
                raise InvalidRequestDataException(f"Ya asignaste una receta para el {category}")
            categories_seen.add(category)

        def save_unique_recipe(meal_data: dict) -> Recipe:
            base_title = meal_data["title"]
            final_title = base_title
            suffix = 1

            while self.recipe_repository.exists_by_user_and_title(user_uid, final_title):
                final_title = f"{base_title} ({suffix})"
                suffix += 1

            recipe = Recipe(
                uid=str(uuid.uuid4()),
                user_uid=user_uid,
                title=final_title,
                duration=meal_data["duration"],
                difficulty=meal_data["difficulty"],
                ingredients=meal_data["ingredients"],
                steps=meal_data["steps"],
                footer=meal_data.get("footer", ""),
                saved_at=datetime.now(),
                generated_by_ai=meal_data.get("generated_by_ai", True),
                category=meal_data["category"],
                image_path=meal_data.get("image_path", None),
                description=meal_data.get("description", ""),
            )

            self.recipe_repository.save(recipe)
            return recipe

        # Asignar recetas por categoría
        breakfast = lunch = dinner = dessert = None

        for meal in meals:
            category = meal["category"]
            recipe = save_unique_recipe(meal)

            if category == "desayuno":
                breakfast = recipe
            elif category == "almuerzo":
                lunch = recipe
            elif category == "cena":
                dinner = recipe
            elif category == "postre":
                dessert = recipe

        meal_plan = DailyMealPlan(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            date_=plan_date,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            dessert=dessert
        )

        self.meal_plan_repository.save(meal_plan)
        return meal_plan
