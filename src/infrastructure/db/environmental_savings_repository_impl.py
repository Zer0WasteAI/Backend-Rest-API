from src.domain.repositories.environmental_savings_repository import EnvironmentalSavingsRepository
from src.domain.models.environmental_savings import EnvironmentalSavings
from src.infrastructure.db.models.environmental_savings_orm import EnvironmentalSavingsORM

from sqlalchemy import insert, select, update
from typing import List, Optional


class EnvironmentalSavingsRepositoryImpl(EnvironmentalSavingsRepository):
    def __init__(self, db):
        self.db = db

    def save(self, savings: EnvironmentalSavings) -> Optional[EnvironmentalSavings]:
        try:
            existing = self.find_by_user_and_recipe(savings.user_uid, savings.recipe_uid)

            if existing:
                stmt = update(EnvironmentalSavingsORM).where(
                    (EnvironmentalSavingsORM.user_uid == savings.user_uid) &
                    (EnvironmentalSavingsORM.recipe_uid == savings.recipe_uid)
                ).values(
                    recipe_title=savings.recipe_title,
                    carbon_footprint=savings.carbon_footprint,
                    water_footprint=savings.water_footprint,
                    energy_footprint=savings.energy_footprint,
                    economic_cost=savings.economic_cost,
                    unit_carbon=savings.unit_carbon,
                    unit_water=savings.unit_water,
                    unit_energy=savings.unit_energy,
                    unit_cost=savings.unit_cost,
                    is_cooked=savings.is_cooked
                )
                self.db.session.execute(stmt)
                print(f"✅ [SAVINGS REPO] Updated savings for recipe {savings.recipe_uid}")
            else:
                stmt = insert(EnvironmentalSavingsORM).values(
                    user_uid=savings.user_uid,
                    recipe_uid=savings.recipe_uid,
                    recipe_title=savings.recipe_title,
                    carbon_footprint=savings.carbon_footprint,
                    water_footprint=savings.water_footprint,
                    energy_footprint=savings.energy_footprint,
                    economic_cost=savings.economic_cost,
                    unit_carbon=savings.unit_carbon,
                    unit_water=savings.unit_water,
                    unit_energy=savings.unit_energy,
                    unit_cost=savings.unit_cost,
                    is_cooked=savings.is_cooked
                )
                self.db.session.execute(stmt)
                print(f"✅ [SAVINGS REPO] Inserted new savings for recipe {savings.recipe_uid}")

            self.db.session.commit()
            return savings

        except Exception as e:
            self.db.session.rollback()
            print(f"🚨 [SAVINGS REPO] Error in save: {str(e)}")
            raise

    def find_by_user(self, user_uid: str) -> List[EnvironmentalSavings]:
        stmt = select(EnvironmentalSavingsORM).where(EnvironmentalSavingsORM.user_uid == user_uid)
        result = self.db.session.execute(stmt)
        return [self._to_domain(row[0]) for row in result.fetchall()]

    def find_by_uid(self, saving_uid: str) -> Optional[EnvironmentalSavings]:
        stmt = select(EnvironmentalSavingsORM).where(EnvironmentalSavingsORM.id == saving_uid)
        result = self.db.session.execute(stmt).fetchone()
        return self._to_domain(result[0]) if result else None

    def find_by_user_and_by_is_cooked(self, user_uid: str, is_cooked: bool) -> List[EnvironmentalSavings]:
        stmt = select(EnvironmentalSavingsORM).where(
            (EnvironmentalSavingsORM.user_uid == user_uid) &
            (EnvironmentalSavingsORM.is_cooked == is_cooked)
        )
        result = self.db.session.execute(stmt)
        return [self._to_domain(row[0]) for row in result.fetchall()]

    def update_type_status(self, saving_uid: str, is_cooked: bool) -> None:
        stmt = update(EnvironmentalSavingsORM).where(
            EnvironmentalSavingsORM.id == saving_uid
        ).values(
            is_cooked=is_cooked
        )
        self.db.session.execute(stmt)
        self.db.session.commit()

    def find_by_user_and_recipe(self, user_uid: str, recipe_uid: str) -> Optional[EnvironmentalSavings]:
        stmt = select(EnvironmentalSavingsORM).where(
            (EnvironmentalSavingsORM.user_uid == user_uid) &
            (EnvironmentalSavingsORM.recipe_uid == recipe_uid)
        )
        result = self.db.session.execute(stmt).fetchone()
        return self._to_domain(result[0]) if result else None

    def _to_domain(self, row: EnvironmentalSavingsORM) -> EnvironmentalSavings:
        return EnvironmentalSavings(
            user_uid=row.user_uid,
            recipe_uid=row.recipe_uid,
            recipe_title=row.recipe_title,
            carbon_footprint=row.carbon_footprint,
            water_footprint=row.water_footprint,
            energy_footprint=row.energy_footprint,
            economic_cost=row.economic_cost,
            unit_carbon=row.unit_carbon,
            unit_water=row.unit_water,
            unit_energy=row.unit_energy,
            unit_cost=row.unit_cost,
            is_cooked=row.is_cooked,
            saved_at=row.saved_at
        )
