from src.infrastructure.ai.gemini_recipe_generator_service import logger
from src.infrastructure.db.base import db
from src.shared.exceptions.custom import RecipeNotFoundException


class RemoveRecipeFromFavoritesUseCase:
    def __init__(self, user_repository, recipe_repository):
        self.UserRepository = user_repository
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str, recipe_uid: str):
        user_orm = self.UserRepository.find_by_uid(user_uid)
        recipe_orm = self.recipe_repository.find_orm_by_id(recipe_uid)

        if not user_orm or not recipe_orm:
            raise RecipeNotFoundException("Usuario o receta no encontrados.")

        if recipe_orm in user_orm.favorite_recipes.all():
            user_orm.favorite_recipes.remove(recipe_orm)

            db.session.commit()
        else:
            logger.info("Intento de eliminar una receta que no estaba en favoritos.")