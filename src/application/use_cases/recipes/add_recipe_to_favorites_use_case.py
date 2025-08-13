from src.shared.exceptions.custom import UserNotFoundException, RecipeNotFoundException
from src.infrastructure.db.base import db

class AddRecipeToFavoritesUseCase:
    def __init__(self, user_repository, recipe_repository):
        self.user_repository = user_repository
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str, recipe_uid: str):
        user = self.user_repository.find_by_uid(user_uid)
        if not user:
            raise UserNotFoundException("Usuario no encontrado.")

        recipe_orm = self.recipe_repository.find_orm_by_id(recipe_uid)
        if not recipe_orm:
            raise RecipeNotFoundException("Receta no encontrada.")

        if recipe_orm not in user.favorite_recipes:
            user.favorite_recipes.append(recipe_orm)

        db.session.commit()