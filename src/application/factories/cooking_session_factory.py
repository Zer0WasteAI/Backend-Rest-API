from src.application.use_cases.cooking_session.start_cooking_session_use_case import StartCookingSessionUseCase
from src.application.use_cases.cooking_session.complete_step_use_case import CompleteStepUseCase
from src.application.use_cases.cooking_session.finish_cooking_session_use_case import FinishCookingSessionUseCase
from src.application.use_cases.recipes.get_mise_en_place_use_case import GetMiseEnPlaceUseCase
from src.infrastructure.db.cooking_session_repository_impl import CookingSessionRepository
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.infrastructure.services.mise_en_place_service import MiseEnPlaceService
from src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_uid import EstimateEnvironmentalSavingsFromRecipeUID
from src.infrastructure.db.base import db

def make_cooking_session_repository():
    return CookingSessionRepository(db)

def make_ingredient_batch_repository():
    return IngredientBatchRepository(db)

def make_recipe_repository():
    return RecipeRepositoryImpl(db)

def make_mise_en_place_service():
    batch_repository = make_ingredient_batch_repository()
    return MiseEnPlaceService(batch_repository)

def make_get_mise_en_place_use_case():
    recipe_repository = make_recipe_repository()
    batch_repository = make_ingredient_batch_repository()
    mise_en_place_service = make_mise_en_place_service()
    
    return GetMiseEnPlaceUseCase(
        recipe_repository=recipe_repository,
        batch_repository=batch_repository,
        mise_en_place_service=mise_en_place_service
    )

def make_start_cooking_session_use_case():
    cooking_session_repository = make_cooking_session_repository()
    recipe_repository = make_recipe_repository()
    
    return StartCookingSessionUseCase(
        cooking_session_repository=cooking_session_repository,
        recipe_repository=recipe_repository
    )

def make_complete_step_use_case():
    cooking_session_repository = make_cooking_session_repository()
    batch_repository = make_ingredient_batch_repository()
    
    return CompleteStepUseCase(
        cooking_session_repository=cooking_session_repository,
        batch_repository=batch_repository
    )

def make_finish_cooking_session_use_case():
    from src.application.factories.environmental_savings_factory import make_estimate_savings_by_uid_use_case
    
    cooking_session_repository = make_cooking_session_repository()
    environmental_savings_use_case = make_estimate_savings_by_uid_use_case()
    
    return FinishCookingSessionUseCase(
        cooking_session_repository=cooking_session_repository,
        environmental_savings_use_case=environmental_savings_use_case
    )