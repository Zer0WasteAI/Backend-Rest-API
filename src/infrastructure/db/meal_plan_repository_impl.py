from typing import Optional
from datetime import date
from sqlalchemy import select, delete
from src.domain.models.daily_meal_plan import DailyMealPlan
from src.domain.repositories.meal_plan_repository import MealPlanRepository
from src.infrastructure.db.models.daily_meal_plan_orm import DailyMealPlanORM
from src.shared.exceptions.custom import MealPlanNotFoundException

class MealPlanRepositoryImpl(MealPlanRepository):
    def __init__(self, db, recipe_mapper):
        self.db = db
        self._map_recipe = recipe_mapper

    def save(self, plan: DailyMealPlan) -> str:
        orm = self.db.session.get(DailyMealPlanORM, plan.uid)
        if orm:
            orm.breakfast_recipe_uid = plan.breakfast.uid if plan.breakfast else None
            orm.lunch_recipe_uid = plan.lunch.uid if plan.lunch else None
            orm.dinner_recipe_uid = plan.dinner.uid if plan.dinner else None
            orm.dessert_recipe_uid = plan.dessert.uid if plan.dessert else None
        else:
            orm = DailyMealPlanORM(
                uid=plan.uid,
                user_uid=plan.user_uid,
                date=plan.date,
                breakfast_recipe_uid=plan.breakfast.uid if plan.breakfast else None,
                lunch_recipe_uid=plan.lunch.uid if plan.lunch else None,
                dinner_recipe_uid=plan.dinner.uid if plan.dinner else None,
                dessert_recipe_uid=plan.dessert.uid if plan.dessert else None
            )
            self.db.session.add(orm)

        self.db.session.commit()
        return plan.uid

    def find_by_user_and_date(self, user_uid: str, target_date: date) -> Optional[DailyMealPlan]:
        stmt = select(DailyMealPlanORM).where(
            DailyMealPlanORM.user_uid == user_uid,
            DailyMealPlanORM.date == target_date
        )
        row = self.db.session.execute(stmt).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def delete_by_user_and_date(self, user_uid: str, target_date: date) -> None:
        stmt = select(DailyMealPlanORM).where(
            DailyMealPlanORM.user_uid == user_uid,
            DailyMealPlanORM.date == target_date
        )
        plan = self.db.session.execute(stmt).scalar_one_or_none()
        if not plan:
            raise MealPlanNotFoundException(f"No se encontró un plan de comidas para el {target_date}")
        self.db.session.delete(plan)
        self.db.session.commit()

    def get_all_by_user(self, user_uid: str) -> list[DailyMealPlan]:
        stmt = select(DailyMealPlanORM).where(DailyMealPlanORM.user_uid == user_uid)
        rows = self.db.session.execute(stmt).scalars().all()
        return [self._to_domain(row) for row in rows]

    def _to_domain(self, row: DailyMealPlanORM) -> DailyMealPlan:
        return DailyMealPlan(
            uid=row.uid,
            user_uid=row.user_uid,
            date_=row.date,
            breakfast=self._map_recipe(row.breakfast_recipe) if row.breakfast_recipe else None,
            lunch=self._map_recipe(row.lunch_recipe) if row.lunch_recipe else None,
            dinner=self._map_recipe(row.dinner_recipe) if row.dinner_recipe else None,
            dessert=self._map_recipe(row.dessert_recipe) if row.dessert_recipe else None,
        )

    def get_all_dates_by_user(self, user_uid: str) -> list[date]:
        stmt = select(DailyMealPlanORM.date).where(DailyMealPlanORM.user_uid == user_uid)
        result = self.db.session.execute(stmt).scalars().all()
        return result

    def update_by_user_and_date(self, plan: DailyMealPlan) -> None:
        stmt = select(DailyMealPlanORM).where(
            DailyMealPlanORM.user_uid == plan.user_uid,
            DailyMealPlanORM.date == plan.date
        )
        orm = self.db.session.execute(stmt).scalar_one_or_none()

        if not orm:
            raise MealPlanNotFoundException(
                f"No existe plan de comidas para el usuario {plan.user_uid} en la fecha {plan.date}")

        orm.breakfast_recipe_uid = plan.breakfast.uid if plan.breakfast else None
        orm.lunch_recipe_uid = plan.lunch.uid if plan.lunch else None
        orm.dinner_recipe_uid = plan.dinner.uid if plan.dinner else None
        orm.dessert_recipe_uid = plan.dessert.uid if plan.dessert else None

        self.db.session.commit()
