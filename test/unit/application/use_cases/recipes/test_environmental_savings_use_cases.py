import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name import EstimateEnvironmentalSavingsFromRecipeName
from src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_uid import EstimateEnvironmentalSavingsFromRecipeUID
from src.application.use_cases.recipes.get_all_environmental_calculations_by_user import GetAllEnvironmentalCalculationsByUser
from src.application.use_cases.recipes.get_environmental_calculations_by_user_and_status import GetEnvironmentalCalculationsByUserAndStatus
from src.application.use_cases.recipes.sum_environmental_calculations_by_user import SumEnvironmentalCalculationsByUser
from src.shared.exceptions.custom import RecipeNotFoundException


def test_estimate_savings_from_recipe_name_saved_recipe():
    recipe_repo = MagicMock()
    generated_repo = MagicMock()
    ai = MagicMock()
    savings_repo = MagicMock()

    recipe = MagicMock()
    recipe.uid = 'r1'
    recipe.ingredients = [MagicMock(name='Tomato', quantity=1, type_unit='pcs')]
    recipe_repo.find_by_user_and_title.return_value = recipe

    ai.estimate_extended_environmental_savings_from_ingredients.return_value = {
        'carbon_footprint': 1.0, 'water_footprint': 2.0, 'energy_footprint': 3.0, 'economic_cost': 4.0,
        'unit_carbon': 'kg', 'unit_water': 'l', 'unit_energy': 'kWh', 'unit_cost': 'S/'
    }

    uc = EstimateEnvironmentalSavingsFromRecipeName(recipe_repo, ai, savings_repo, generated_repo)
    res = uc.execute('u1', 'Any')
    assert res['recipe_uid'] == 'r1'
    savings_repo.save.assert_called_once()


def test_estimate_savings_from_recipe_uid():
    recipe_repo = MagicMock()
    ai = MagicMock()
    savings_repo = MagicMock()
    recipe = MagicMock()
    recipe.uid = 'r1'
    recipe.user_uid = 'u1'
    recipe.title = 'T'
    recipe.ingredients = []
    recipe_repo.find_by_uid.return_value = recipe
    ai.estimate_extended_environmental_savings_from_ingredients.return_value = {
        'carbon_footprint': 1.0, 'water_footprint': 2.0, 'energy_footprint': 3.0, 'economic_cost': 4.0,
        'unit_carbon': 'kg', 'unit_water': 'l', 'unit_energy': 'kWh', 'unit_cost': 'S/'
    }
    uc = EstimateEnvironmentalSavingsFromRecipeUID(recipe_repo, ai, savings_repo)
    res = uc.execute('r1')
    assert res['recipe_uid'] == 'r1'
    savings_repo.save.assert_called_once()


def test_get_all_environmental_calculations_by_user():
    repo = MagicMock()
    calc = MagicMock()
    calc.recipe_uid = 'r1'
    calc.recipe_title = 'T'
    calc.carbon_footprint = 1.0
    calc.water_footprint = 2.0
    calc.energy_footprint = 3.0
    calc.economic_cost = 4.0
    calc.unit_carbon = 'kg'
    calc.unit_water = 'l'
    calc.unit_energy = 'kWh'
    calc.unit_cost = 'S/'
    calc.is_cooked = False
    calc.saved_at = datetime.now()
    repo.find_by_user.return_value = [calc]
    uc = GetAllEnvironmentalCalculationsByUser(repo)
    res = uc.execute('u1')
    assert res[0]['recipe_uid'] == 'r1'


def test_get_environmental_calculations_by_user_and_status():
    repo = MagicMock()
    calc = MagicMock()
    calc.recipe_uid = 'r1'
    calc.recipe_title = 'T'
    calc.carbon_footprint = 1.0
    calc.water_footprint = 2.0
    calc.energy_footprint = 3.0
    calc.economic_cost = 4.0
    calc.unit_carbon = 'kg'
    calc.unit_water = 'l'
    calc.unit_energy = 'kWh'
    calc.unit_cost = 'S/'
    calc.is_cooked = True
    calc.saved_at = datetime.now()
    repo.find_by_user_and_by_is_cooked.return_value = [calc]
    uc = GetEnvironmentalCalculationsByUserAndStatus(repo)
    res = uc.execute('u1', True)
    assert res[0]['is_cooked'] is True


def test_sum_environmental_calculations_by_user():
    repo = MagicMock()
    calc = MagicMock()
    calc.carbon_footprint = 1.2
    calc.water_footprint = 3.4
    calc.energy_footprint = 5.6
    calc.economic_cost = 7.8
    calc.unit_carbon = 'kg'
    calc.unit_water = 'l'
    calc.unit_energy = 'kWh'
    calc.unit_cost = 'S/'
    repo.find_by_user.return_value = [calc]
    uc = SumEnvironmentalCalculationsByUser(repo)
    res = uc.execute('u1')
    assert res['total_carbon_footprint'] == round(1.2, 2)

