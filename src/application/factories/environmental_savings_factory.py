from src.infrastructure.db.base import db
from src.infrastructure.db.environmental_savings_repository_impl import EnvironmentalSavingsRepositoryImpl
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.infrastructure.db.recipe_generated_repository_impl import RecipeGeneratedRepositoryImpl
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService

from src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_uid import EstimateEnvironmentalSavingsFromRecipeUID
from src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name import EstimateEnvironmentalSavingsFromRecipeName
from src.application.use_cases.recipes.get_all_environmental_calculations_by_user import GetAllEnvironmentalCalculationsByUser
from src.application.use_cases.recipes.get_environmental_calculations_by_user_and_status import GetEnvironmentalCalculationsByUserAndStatus
from src.application.use_cases.recipes.sum_environmental_calculations_by_user import SumEnvironmentalCalculationsByUser


def make_environmental_savings_repository():
    return EnvironmentalSavingsRepositoryImpl(db)

def make_recipe_generated_repository():
    return RecipeGeneratedRepositoryImpl()


def make_estimate_savings_by_uid_use_case():
    return EstimateEnvironmentalSavingsFromRecipeUID(
        recipe_repository=RecipeRepositoryImpl(db),
        ai_adapter=GeminiAdapterService(),
        savings_repository=make_environmental_savings_repository()
    )


def make_estimate_savings_by_title_use_case():
    return EstimateEnvironmentalSavingsFromRecipeName(
        recipe_repository=RecipeRepositoryImpl(db),
        ai_adapter=GeminiAdapterService(),
        savings_repository=make_environmental_savings_repository(),
        recipe_generated_repository=make_recipe_generated_repository()
    )


def make_get_all_environmental_calculations_use_case():
    return GetAllEnvironmentalCalculationsByUser(
        savings_repository=make_environmental_savings_repository()
    )


def make_get_environmental_calculations_by_status_use_case():
    return GetEnvironmentalCalculationsByUserAndStatus(
        savings_repository=make_environmental_savings_repository()
    )

def make_sum_environmental_calculations_by_user():
    return SumEnvironmentalCalculationsByUser(EnvironmentalSavingsRepositoryImpl(db))
