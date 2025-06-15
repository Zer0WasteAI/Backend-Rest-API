from datetime import date
from src.domain.models.daily_meal_plan import DailyMealPlan
from src.shared.exceptions.custom import MealPlanNotFoundException

class GetMealPlanByUserAndDateUseCase:
    def __init__(self, meal_plan_repository):
        self.meal_plan_repository = meal_plan_repository

    def execute(self, user_uid: str, plan_date: date) -> DailyMealPlan:
        plan = self.meal_plan_repository.find_by_user_and_date(user_uid, plan_date)
        if not plan:
            raise MealPlanNotFoundException(f"No hay plan de comidas para el {plan_date}")
        return plan
