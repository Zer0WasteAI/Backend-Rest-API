from typing import List
from datetime import date

class GetMealPlanDatesUseCase:
    def __init__(self, meal_plan_repository):
        self.meal_plan_repository = meal_plan_repository

    def execute(self, user_uid: str) -> List[date]:
        return self.meal_plan_repository.get_all_dates_by_user(user_uid)
