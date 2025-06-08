from src.domain.models.daily_meal_plan import DailyMealPlan
from typing import List

class GetAllMealPlansByUserUseCase:
    def __init__(self, meal_plan_repository):
        self.meal_plan_repository = meal_plan_repository

    def execute(self, user_uid: str) -> List[DailyMealPlan]:
        return self.meal_plan_repository.get_all_by_user(user_uid)
