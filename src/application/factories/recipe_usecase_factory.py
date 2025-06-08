from src.application.use_cases.recipes.generate_recipes_use_case import GenerateRecipesUseCase
from src.application.use_cases.recipes.prepare_recipe_generation_data_use_case import PrepareRecipeGenerationDataUseCase
from src.application.use_cases.recipes.generate_custom_recipe_use_case import GenerateCustomRecipeUseCase
from src.application.use_cases.recipes.save_recipe_use_case import SaveRecipeUseCase
from src.application.use_cases.recipes.get_saved_recipes_use_case import GetSavedRecipesUseCase
from src.application.use_cases.recipes.get_all_recipes_use_case import GetAllRecipesUseCase
from src.application.use_cases.recipes.delete_user_recipe_use_case import DeleteUserRecipeUseCase
from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
from src.infrastructure.db.base import db

def make_prepare_recipe_generation_data_use_case():
    return PrepareRecipeGenerationDataUseCase(InventoryRepositoryImpl(db))

def make_generate_recipes_use_case():
    return GenerateRecipesUseCase(GeminiRecipeGeneratorService())

def make_generate_custom_recipe_use_case():
    return GenerateCustomRecipeUseCase(GeminiRecipeGeneratorService())

def make_save_recipe_use_case():
    return SaveRecipeUseCase(RecipeRepositoryImpl(db))

def make_get_saved_recipes_use_case():
    return GetSavedRecipesUseCase(RecipeRepositoryImpl(db))

def make_get_all_recipes_use_case():
    return GetAllRecipesUseCase(RecipeRepositoryImpl(db))

def make_delete_user_recipe_use_case():
    return DeleteUserRecipeUseCase(RecipeRepositoryImpl(db))