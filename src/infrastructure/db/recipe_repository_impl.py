from typing import List, Optional
from sqlalchemy import select, delete
from src.domain.models.recipe import Recipe
from src.domain.repositories.recipe_repository import RecipeRepository
from src.infrastructure.db.models.recipe_orm import RecipeORM

class RecipeRepositoryImpl(RecipeRepository):
    def __init__(self, db):
        self.db = db

    def save(self, recipe: Recipe) -> None:
        recipe_orm = RecipeORM(
            uid=recipe.uid,
            user_uid=recipe.user_uid,
            title=recipe.title,
            duration=recipe.duration,
            difficulty=recipe.difficulty,
            ingredients=recipe.ingredients,
            steps=recipe.steps,
            footer=recipe.footer,
            is_custom=recipe.is_custom,
            saved_at=recipe.saved_at
        )
        self.db.session.add(recipe_orm)
        self.db.session.commit()

    def get_by_uid(self, recipe_uid: str) -> Optional[Recipe]:
        recipe_orm = self.db.session.get(RecipeORM, recipe_uid)
        if not recipe_orm:
            return None

        return Recipe(
            uid=recipe_orm.uid,
            user_uid=recipe_orm.user_uid,
            title=recipe_orm.title,
            duration=recipe_orm.duration,
            difficulty=recipe_orm.difficulty,
            ingredients=recipe_orm.ingredients,
            steps=recipe_orm.steps,
            footer=recipe_orm.footer,
            is_custom=recipe_orm.is_custom,
            saved_at=recipe_orm.saved_at
        )

    def get_saved_by_user(self, user_uid: str) -> List[Recipe]:
        stmt = select(RecipeORM).where(RecipeORM.user_uid == user_uid).order_by(RecipeORM.saved_at.desc())
        recipe_orms = self.db.session.execute(stmt).scalars().all()

        recipes = []
        for recipe_orm in recipe_orms:
            recipe = Recipe(
                uid=recipe_orm.uid,
                user_uid=recipe_orm.user_uid,
                title=recipe_orm.title,
                duration=recipe_orm.duration,
                difficulty=recipe_orm.difficulty,
                ingredients=recipe_orm.ingredients,
                steps=recipe_orm.steps,
                footer=recipe_orm.footer,
                is_custom=recipe_orm.is_custom,
                saved_at=recipe_orm.saved_at
            )
            recipes.append(recipe)

        return recipes

    def delete(self, recipe_uid: str) -> None:
        stmt = delete(RecipeORM).where(RecipeORM.uid == recipe_uid)
        self.db.session.execute(stmt)
        self.db.session.commit()

    def exists_by_user_and_title(self, user_uid: str, title: str) -> bool:
        stmt = select(RecipeORM).where(
            RecipeORM.user_uid == user_uid,
            RecipeORM.title == title
        )
        result = self.db.session.execute(stmt).scalar_one_or_none()
        return result is not None 