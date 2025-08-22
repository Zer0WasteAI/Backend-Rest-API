from src.application.use_cases.recipes.add_recipe_to_favorites_use_case import AddRecipeToFavoritesUseCase
from src.application.use_cases.recipes.generate_recipes_use_case import GenerateRecipesUseCase
from src.application.use_cases.recipes.get_favorite_recipes_use_case import GetFavoriteRecipesUseCase
from src.application.use_cases.recipes.prepare_recipe_generation_data_use_case import PrepareRecipeGenerationDataUseCase
from src.application.use_cases.recipes.generate_custom_recipe_use_case import GenerateCustomRecipeUseCase
from src.application.use_cases.recipes.remove_recipe_from_favorites_use_case import RemoveRecipeFromFavoritesUseCase
from src.application.use_cases.recipes.save_recipe_use_case import SaveRecipeUseCase
from src.application.use_cases.recipes.get_saved_recipes_use_case import GetSavedRecipesUseCase
from src.application.use_cases.recipes.get_all_recipes_use_case import GetAllRecipesUseCase
from src.application.use_cases.recipes.delete_user_recipe_use_case import DeleteUserRecipeUseCase
from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.infrastructure.db.user_repository import UserRepository
from src.application.services.recipe_image_generator_service import RecipeImageGeneratorService
from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.db.base import db

def make_prepare_recipe_generation_data_use_case():
    return PrepareRecipeGenerationDataUseCase(InventoryRepositoryImpl(db))

def make_generate_recipes_use_case():
    return GenerateRecipesUseCase(GeminiRecipeGeneratorService())

def make_generate_custom_recipe_use_case():
    recipe_service = GeminiRecipeGeneratorService()
    return GenerateCustomRecipeUseCase(recipe_service)

def make_save_recipe_use_case():
    return SaveRecipeUseCase(RecipeRepositoryImpl(db))

def make_get_saved_recipes_use_case():
    return GetSavedRecipesUseCase(RecipeRepositoryImpl(db))

def make_get_all_recipes_use_case():
    return GetAllRecipesUseCase(RecipeRepositoryImpl(db))

def make_delete_user_recipe_use_case():
    return DeleteUserRecipeUseCase(RecipeRepositoryImpl(db))

def make_recipe_image_generator_service():
    return RecipeImageGeneratorService(
        ai_service=GeminiRecipeGeneratorService(),
        storage_adapter=FirebaseStorageAdapter(),
        ai_image_service=GeminiAdapterService()
    )

def make_add_recipe_to_favorites_use_case():
    return AddRecipeToFavoritesUseCase(
        user_repository=UserRepository(),
        recipe_repository=RecipeRepositoryImpl(db)
    )

def make_get_favorite_recipes_use_case():
    return GetFavoriteRecipesUseCase(
        user_repository=UserRepository(),
        recipe_repository=RecipeRepositoryImpl(db)
    )

def make_remove_recipe_from_favorites_use_case():
    return RemoveRecipeFromFavoritesUseCase(
        user_repository=UserRepository(),
        recipe_repository=RecipeRepositoryImpl(db)
    )
