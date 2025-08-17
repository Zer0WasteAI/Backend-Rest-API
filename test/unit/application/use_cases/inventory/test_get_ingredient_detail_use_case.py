import pytest
from unittest.mock import MagicMock
import types
from datetime import datetime, timezone, timedelta

from src.application.use_cases.inventory.get_ingredient_detail_use_case import GetIngredientDetailUseCase


def test_get_ingredient_detail_success(monkeypatch):
    # Build Inventory with one ingredient and two stacks
    from src.domain.models.inventory import Inventory
    from src.domain.models.ingredient import Ingredient, IngredientStack

    inv = Inventory('u1')
    ing = Ingredient('Tomato', 'g', 'fridge', tips='wash', image_path='')
    ing.add_stack(IngredientStack(10, 'g', datetime.now(timezone.utc) - timedelta(days=1), datetime.now(timezone.utc) + timedelta(days=3)))
    ing.add_stack(IngredientStack(5, 'g', datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=1)))
    inv.ingredients['Tomato'] = ing

    repo = MagicMock()
    repo.get_by_user_uid.return_value = inv

    # Patch AI adapter to avoid external calls
    fake_module = types.SimpleNamespace(GeminiAdapterService=lambda: types.SimpleNamespace(
        analyze_environmental_impact=lambda *a, **k: {"environmental_impact": {}},
        generate_utilization_ideas=lambda *a, **k: {"utilization_ideas": []},
        generate_consumption_advice=lambda *a, **k: {"consumption_advice": {}, "before_consumption_advice": {}}
    ))
    monkeypatch.setitem(__import__('sys').modules, 'src.infrastructure.ai.gemini_adapter_service', fake_module)

    uc = GetIngredientDetailUseCase(repo)
    res = uc.execute('u1', 'Tomato')
    assert res['name'] == 'Tomato'
    assert res['stack_count'] == 2
    assert 'environmental_impact' in res


def test_get_ingredient_detail_missing_inventory_raises():
    repo = MagicMock()
    repo.get_by_user_uid.return_value = None
    uc = GetIngredientDetailUseCase(repo)
    with pytest.raises(ValueError):
        uc.execute('u1', 'Tomato')


def test_get_ingredient_detail_missing_ingredient_raises():
    from src.domain.models.inventory import Inventory
    inv = Inventory('u1')
    repo = MagicMock()
    repo.get_by_user_uid.return_value = inv
    uc = GetIngredientDetailUseCase(repo)
    with pytest.raises(ValueError):
        uc.execute('u1', 'Tomato')

