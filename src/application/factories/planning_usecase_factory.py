from src.application.use_cases.planning.save_meal_plan_use_case import SaveMealPlanUseCase
from src.application.use_cases.planning.update_meal_plan_use_case import UpdateMealPlanUseCase
from src.application.use_cases.planning.delete_meal_plan_use_case import DeleteMealPlanUseCase
from src.application.use_cases.planning.get_meal_plan_by_user_and_date_use_case import GetMealPlanByUserAndDateUseCase
from src.application.use_cases.planning.get_all_meal_plans_by_user_use_case import GetAllMealPlansByUserUseCase
from src.application.use_cases.planning.get_meal_plan_dates_usecase import GetMealPlanDatesUseCase

from src.infrastructure.db.meal_plan_repository_impl import MealPlanRepositoryImpl
from src.infrastructure.db.recipe_repository_impl import RecipeRepositoryImpl
from src.infrastructure.db.base import db

# Repositorios compartidos
recipe_repository = RecipeRepositoryImpl(db)
recipe_mapper = recipe_repository.map_to_domain
meal_plan_repository = MealPlanRepositoryImpl(db, recipe_mapper)

def make_save_meal_plan_use_case():
    return SaveMealPlanUseCase(meal_plan_repository, recipe_repository)

def make_update_meal_plan_use_case():
    return UpdateMealPlanUseCase(meal_plan_repository, recipe_repository)

def make_delete_meal_plan_use_case():
    return DeleteMealPlanUseCase(meal_plan_repository)

def make_get_meal_plan_by_date_use_case():
    return GetMealPlanByUserAndDateUseCase(meal_plan_repository)

def make_get_all_meal_plans_use_case():
    return GetAllMealPlansByUserUseCase(meal_plan_repository)

def make_get_meal_plan_dates_use_case():
    return GetMealPlanDatesUseCase(meal_plan_repository)
