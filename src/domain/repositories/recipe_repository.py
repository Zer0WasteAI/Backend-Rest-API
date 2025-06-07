from abc import ABC, abstractmethod
from src.domain.models.recipe import Recipe

class RecipeRepository(ABC):
    @abstractmethod
    def save(self, recipe: Recipe) -> str:
        pass

    @abstractmethod
    def find_by_uid(self, uid: str) -> Optional[Recipe]:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Recipe]:
        pass

    @abstractmethod
    def find_best_match_name(self, name_query: str) -> Optional[Recipe]:
        pass