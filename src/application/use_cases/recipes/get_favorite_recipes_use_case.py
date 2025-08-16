from src.infrastructure.db.schemas.user_schema import User
from src.domain.models.recipe import Recipe
from src.shared.exceptions.custom import UserNotFoundException


class GetFavoriteRecipesUseCase:
    def __init__(self, user_repository, recipe_repository):
        self.UserRepository = user_repository
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str) -> list[Recipe]:
        user_orm = self.UserRepository.find_by_uid(user_uid)
        if not user_orm:
            raise UserNotFoundException("Usuario no encontrado.")

        favorite_recipes_query = user_orm.favorite_recipes

        favorite_recipes_orm_list = favorite_recipes_query.all()

        domain_recipes = [
            self.recipe_repository.map_to_domain(recipe_orm)
            for recipe_orm in favorite_recipes_orm_list
        ]

        return domain_recipes
