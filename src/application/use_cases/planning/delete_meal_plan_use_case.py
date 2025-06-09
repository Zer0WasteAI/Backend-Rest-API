from datetime import date
from src.shared.exceptions.custom import MealPlanNotFoundException

class DeleteMealPlanUseCase:
    def __init__(self, meal_plan_repository):
        self.meal_plan_repository = meal_plan_repository

    def execute(self, user_uid: str, plan_date: date) -> None:
        existing_plan = self.meal_plan_repository.find_by_user_and_date(user_uid, plan_date)
        if not existing_plan:
            raise MealPlanNotFoundException(f"No existe plan de comidas para el {plan_date}")

        self.meal_plan_repository.delete_by_user_and_date(user_uid, plan_date)