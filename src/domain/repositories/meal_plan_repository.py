from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from src.domain.models.daily_meal_plan import DailyMealPlan

class MealPlanRepository(ABC):
    @abstractmethod
    def save(self, plan: DailyMealPlan) -> str:
        pass

    @abstractmethod
    def find_by_user_and_date(self, user_uid: str, target_date: date) -> Optional[DailyMealPlan]:
        pass

    @abstractmethod
    def delete_by_user_and_date(self, user_uid: str, target_date: date) -> None:
        pass

    @abstractmethod
    def get_all_by_user(self, user_uid: str) -> list[DailyMealPlan]:
        pass

    @abstractmethod
    def get_all_dates_by_user(self, user_uid: str) -> list[date]:
        pass

