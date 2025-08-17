import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.application.use_cases.recipes.generate_recipes_use_case import GenerateRecipesUseCase
from src.application.use_cases.recipes.prepare_recipe_generation_data_use_case import PrepareRecipeGenerationDataUseCase


def test_generate_recipes_use_case_calls_service():
    service = MagicMock()
    service.generate_recipes.return_value = {"generated_recipes": []}
    uc = GenerateRecipesUseCase(service)
    data = {"ingredients": []}
    res = uc.execute(data, num_recipes=3, recipe_categories=['vegan'])
    assert res == {"generated_recipes": []}
    service.generate_recipes.assert_called_once()


@patch('src.application.use_cases.recipes.prepare_recipe_generation_data_use_case.make_firestore_profile_service')
def test_prepare_recipe_generation_data_filters_allergies(mock_fs_service):
    # Inventory with one allergic ingredient and one ok
    from src.domain.models.inventory import Inventory
    from src.domain.models.ingredient import Ingredient, IngredientStack
    inv = Inventory('u1')
    ing1 = Ingredient('Peanut', 'g', 'pantry', tips='', image_path='')
    ing1.add_stack(IngredientStack(100, 'g', datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=1)))
    ing2 = Ingredient('Tomato', 'g', 'fridge', tips='', image_path='')
    ing2.add_stack(IngredientStack(100, 'g', datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=10)))
    inv.ingredients = {'Peanut': ing1, 'Tomato': ing2}

    repo = MagicMock()
    repo.get_by_user_uid.return_value = inv

    mock_profile = {
        'allergies': ['peanut'],
        'allergyItems': [],
        'preferredFoodTypes': ['italian'],
        'specialDietItems': ['vegan'],
        'cookingLevel': 'beginner',
    }
    mock_fs_service.return_value.get_profile.return_value = mock_profile

    uc = PrepareRecipeGenerationDataUseCase(repo)
    result = uc.execute('u1')
    names = [i['name'].lower() for i in result['ingredients']]
    assert 'peanut' not in names
    assert 'tomato' in names
    assert 'italian' in result['preferences']
