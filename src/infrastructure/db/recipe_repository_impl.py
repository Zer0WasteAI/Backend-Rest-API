from rapidfuzz import process
from typing import Optional
from sqlalchemy import select
from src.domain.models.recipe import Recipe, RecipeIngredient
from src.domain.repositories.recipe_repository import RecipeRepository
from src.infrastructure.db.models.recipe_orm import (
    RecipeORM,
    RecipeIngredientORM,
    RecipeStepORM
)

class RecipeRepositoryImpl(RecipeRepository):
    def __init__(self, db):
        self.db = db

    def save(self, recipe: Recipe) -> str:
        orm = RecipeORM(
            uid=recipe.uid,
            title=recipe.title,
            duration=recipe.duration,
            difficulty=recipe.difficulty,
            footer=recipe.footer,
            user_uid=recipe.user_uid,
            generated_by_ai=recipe.generated_by_ai
        )
        self.db.session.add(orm)

        for ingredient in recipe.ingredients:
            ingredient_orm = RecipeIngredientORM(
                name=ingredient.name,
                quantity=ingredient.quantity,
                type_unit=ingredient.type_unit,
                recipe_uid=recipe.uid
            )
            self.db.session.add(ingredient_orm)

        for idx, step in enumerate(recipe.steps):
            step_orm = RecipeStepORM(
                step_number=idx + 1,
                description=step,
                recipe_uid=recipe.uid
            )
            self.db.session.add(step_orm)

        self.db.session.commit()
        return recipe.uid

    def find_by_uid(self, uid: str) -> Optional[Recipe]:
        recipe_row = self.db.session.get(RecipeORM, uid)
        if not recipe_row:
            return None

        ingredients = self.db.session.execute(
            select(RecipeIngredientORM).where(RecipeIngredientORM.recipe_uid == uid)
        ).scalars().all()

        steps = self.db.session.execute(
            select(RecipeStepORM).where(RecipeStepORM.recipe_uid == uid).order_by(RecipeStepORM.step_number)
        ).scalars().all()

        domain_ingredients = [
            RecipeIngredient(i.name, i.quantity, i.type_unit) for i in ingredients
        ]
        domain_steps = [s.description for s in steps]

        return Recipe(
            uid=recipe_row.uid,
            title=recipe_row.title,
            duration=recipe_row.duration,
            difficulty=recipe_row.difficulty,
            footer=recipe_row.footer,
            ingredients=domain_ingredients,
            steps=domain_steps,
            user_uid=recipe_row.user_uid,
            generated_by_ai=recipe_row.generated_by_ai
        )

    def find_by_name(self, name: str) -> Optional[Recipe]:
        stmt = select(RecipeORM).where(RecipeORM.title == name)
        row = self.db.session.execute(stmt).scalar_one_or_none()
        return self.find_by_uid(row.uid) if row else None

    def find_best_match_name(self, name_query: str) -> Optional[Recipe]:
        all_recipes = self.db.session.execute(select(RecipeORM)).scalars().all()
        if not all_recipes:
            return None
        options = [(r.title, r.uid) for r in all_recipes]
        best_match, score, _ = process.extractOne(name_query, [t for t, _ in options])
        if score < 80:
            return None
        matched_uid = next(uid for title, uid in options if title == best_match)
        return self.find_by_uid(matched_uid)

    from typing import List

    def find_by_user_uid(self, user_uid: str) -> List[Recipe]:
        stmt = select(RecipeORM).where(RecipeORM.user_uid == user_uid)
        rows = self.db.session.execute(stmt).scalars().all()

        recipes = []
        for row in rows:
            ingredients = self.db.session.execute(
                select(RecipeIngredientORM).where(RecipeIngredientORM.recipe_uid == row.uid)
            ).scalars().all()

            steps = self.db.session.execute(
                select(RecipeStepORM).where(RecipeStepORM.recipe_uid == row.uid).order_by(RecipeStepORM.step_number)
            ).scalars().all()

            domain_ingredients = [
                RecipeIngredient(i.name, i.quantity, i.type_unit) for i in ingredients
            ]
            domain_steps = [s.description for s in steps]

            recipe = Recipe(
                uid=row.uid,
                title=row.title,
                duration=row.duration,
                difficulty=row.difficulty,
                footer=row.footer,
                ingredients=domain_ingredients,
                steps=domain_steps,
                user_uid=row.user_uid,
                generated_by_ai=row.generated_by_ai
            )
            recipes.append(recipe)

        return recipes

