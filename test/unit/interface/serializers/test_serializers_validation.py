import pytest


def test_recipe_custom_request_schema_validation():
    from src.interface.serializers.recipe_serializers import CustomRecipeRequestSchema
    schema = CustomRecipeRequestSchema()
    ok = schema.load({"ingredients": ["tomato"], "num_recipes": 2})
    assert ok["ingredients"] == ["tomato"]
    with pytest.raises(Exception):
        schema.load({"ingredients": []})


def test_recipe_save_request_schema_validation():
    from src.interface.serializers.recipe_serializers import SaveRecipeRequestSchema
    schema = SaveRecipeRequestSchema()
    payload = {
        "title": "T", "duration": "10m", "difficulty": "Fácil",
        "ingredients": [{"name": "Tomate", "quantity": 1, "type_unit": "pcs"}],
        "steps": [{"step_order": 1, "description": "Paso"}],
        "generated_by_ai": True,
        "category": "ensalada",
        "description": "desc"
    }
    ok = schema.load(payload)
    assert ok["title"] == "T"
    with pytest.raises(Exception):
        schema.load({**payload, "difficulty": "Impossible"})


def test_inventory_add_item_serializer_validation():
    from src.interface.serializers.add_item_serializer import AddItemToInventorySchema
    schema = AddItemToInventorySchema()
    base = {
        "name": "Tomate",
        "quantity": 1.0,
        "unit": "g",
        "storage_type": "frigorifico",
        "category": "ingredient",
    }
    ok = schema.load(base)
    assert ok["name"] == "Tomate"
    with pytest.raises(Exception):
        schema.load({**base, "unit": "invalid"})


def test_mark_consumed_serializers():
    from src.interface.serializers.mark_consumed_serializer import MarkIngredientConsumedSchema, MarkFoodConsumedSchema
    ing_schema = MarkIngredientConsumedSchema()
    food_schema = MarkFoodConsumedSchema()
    assert ing_schema.load({"consumed_quantity": 0.5})["consumed_quantity"] == 0.5
    assert food_schema.load({}) == {"consumed_portions": None}
    with pytest.raises(Exception):
        ing_schema.load({"consumed_quantity": 0})


def test_inventory_batch_update_schemas():
    from src.interface.serializers.inventory_serializers import UpdateIngredientQuantitySchema, UpdateFoodQuantitySchema
    ing_q = UpdateIngredientQuantitySchema()
    food_q = UpdateFoodQuantitySchema()
    assert ing_q.load({"quantity": 1.0})["quantity"] == 1.0
    with pytest.raises(Exception):
        ing_q.load({"quantity": -1})
    assert food_q.load({"serving_quantity": 1})["serving_quantity"] == 1
    with pytest.raises(Exception):
        food_q.load({"serving_quantity": 0})

