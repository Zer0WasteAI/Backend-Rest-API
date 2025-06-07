from typing import Optional
from sqlalchemy import select
from src.domain.models.recipe import Recipe, RecipeIngredient, RecipeStep
from src.domain.repositories.recipe_repository import RecipeRepository
from src.infrastructure.db.models.recipe_orm import RecipeORM
from src.infrastructure.db.models.recipe_ingredient_orm import RecipeIngredientORM
from src.infrastructure.db.models.recipe_step_orm import RecipeStepORM
from rapidfuzz import process

class RecipeRepositoryImpl(RecipeRepository):
    def __init__(self, db):
        self.db = db

    def save(self, recipe: Recipe) -> str:
        # Crear y agregar la receta base
        recipe_orm = RecipeORM(
            uid=recipe.uid,
            title=recipe.title,
            duration=recipe.duration,
            difficulty=recipe.difficulty,
            footer=recipe.footer,
            user_uid=recipe.user_uid,
            generated_by_ai=recipe.generated_by_ai
        )
        self.db.session.add(recipe_orm)

        # Agregar los ingredientes
        for ing in recipe.ingredients:
            ing_orm = RecipeIngredientORM(
                recipe_uid=recipe.uid,
                name=ing.name,
                quantity=ing.quantity,
                type_unit=ing.type_unit
            )
            self.db.session.add(ing_orm)

        # Agregar los pasos
        for step in recipe.steps:
            step_orm = RecipeStepORM(
                recipe_uid=recipe.uid,
                step_order=step.step_order,
                description=step.description
            )
            self.db.session.add(step_orm)

        self.db.session.commit()
        return recipe.uid

    def find_by_uid(self, uid: str) -> Optional[Recipe]:
        recipe_row = self.db.session.get(RecipeORM, uid)
        if not recipe_row:
            return None

        domain_ingredients = [
            RecipeIngredient(i.name, i.quantity, i.type_unit)
            for i in recipe_row.ingredients
        ]

        domain_steps = sorted(
            [RecipeStep(s.step_order, s.description) for s in recipe_row.steps],
            key=lambda s: s.step_order
        )

        return Recipe(
            uid=recipe_row.uid,
            user_uid=recipe_row.user_uid,
            title=recipe_row.title,
            duration=recipe_row.duration,
            difficulty=recipe_row.difficulty,
            ingredients=domain_ingredients,
            steps=domain_steps,
            footer=recipe_row.footer,
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
