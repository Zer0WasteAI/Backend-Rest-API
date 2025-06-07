from typing import Optional
from src.domain.models.recipe import Recipe
from src.domain.repositories.recipe_repository import RecipeRepository
class RecipeRepositoryImpl(RecipeRepository):
    def __init__(self, db):
        self.db = db
    def save(self, recipe: Recipe) -> str:
        return 'a'

    # TODO: all that xd

    def find_by_uid(self, uid: str) -> Optional[Recipe]:
        return None

    def find_by_name(self, name: str) -> Optional[Recipe]:
        return None

    def find_best_match_name(self, name_query: str) -> Optional[Recipe]:
        return None