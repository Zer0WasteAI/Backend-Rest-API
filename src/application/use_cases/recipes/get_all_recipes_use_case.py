from typing import List
from src.domain.models.recipe import Recipe

class GetAllRecipesUseCase:
    def __init__(self, recipe_repository):
        self.recipe_repository = recipe_repository

    def execute(self) -> List[Recipe]:
        return self.recipe_repository.get_all()