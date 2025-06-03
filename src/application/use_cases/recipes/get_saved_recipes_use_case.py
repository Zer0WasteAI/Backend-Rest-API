from typing import List
from src.domain.models.recipe import Recipe

class GetSavedRecipesUseCase:
    def __init__(self, recipe_repository):
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str) -> List[Recipe]:
        return self.recipe_repository.get_saved_by_user(user_uid) 