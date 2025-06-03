from typing import List, Optional
from abc import ABC, abstractmethod
from src.domain.models.recipe import Recipe

class RecipeRepository(ABC):
    @abstractmethod
    def save(self, recipe: Recipe) -> None:
        pass

    @abstractmethod
    def get_by_uid(self, recipe_uid: str) -> Optional[Recipe]:
        pass

    @abstractmethod
    def get_saved_by_user(self, user_uid: str) -> List[Recipe]:
        pass

    @abstractmethod
    def delete(self, recipe_uid: str) -> None:
        pass

    @abstractmethod
    def exists_by_user_and_title(self, user_uid: str, title: str) -> bool:
        pass 