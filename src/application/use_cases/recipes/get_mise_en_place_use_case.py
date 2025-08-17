from typing import Optional
from src.domain.models.mise_en_place import MiseEnPlace
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository
from src.infrastructure.services.mise_en_place_service import MiseEnPlaceService
from src.shared.exceptions.custom import RecipeNotFoundException

class GetMiseEnPlaceUseCase:
    def __init__(
        self,
        recipe_repository: RecipeRepositoryImpl,
        batch_repository: IngredientBatchRepository,
        mise_en_place_service: MiseEnPlaceService
    ):
        self.recipe_repository = recipe_repository
        self.batch_repository = batch_repository
        self.mise_en_place_service = mise_en_place_service

    def execute(self, recipe_uid: str, servings: int, user_uid: str) -> MiseEnPlace:
        """
        Generate mise en place for a recipe with specified servings.
        
        Args:
            recipe_uid: UID of the recipe
            servings: Number of servings to prepare for
            user_uid: UID of the user (for FEFO lot suggestions)
            
        Returns:
            MiseEnPlace object with tools, prep tasks, and ingredient suggestions
            
        Raises:
            RecipeNotFoundException: If recipe is not found
            ValueError: If servings <= 0
        """
        if servings <= 0:
            raise ValueError("Servings must be positive")
        
        # Get the recipe
        recipe = self.recipe_repository.find_by_uid(recipe_uid)
        if not recipe:
            raise RecipeNotFoundException(f"Recipe with UID {recipe_uid} not found")
        
        # Generate mise en place
        mise_en_place = self.mise_en_place_service.generate_mise_en_place(
            recipe=recipe,
            servings=servings,
            user_uid=user_uid
        )
        
        return mise_en_place