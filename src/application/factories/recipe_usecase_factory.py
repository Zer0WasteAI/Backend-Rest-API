from src.application.use_cases.recipes.generate_recipes_use_case import GenerateRecipesUseCase
from src.application.use_cases.recipes.prepare_recipe_generation_data_use_case import PrepareRecipeGenerationDataUseCase
from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
from src.infrastructure.db.base import db

def make_prepare_recipe_generation_data_use_case():
    return PrepareRecipeGenerationDataUseCase(InventoryRepositoryImpl(db))

def make_generate_recipes_use_case():
    return GenerateRecipesUseCase(GeminiRecipeGeneratorService())