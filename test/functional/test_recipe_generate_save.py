import pytest


def test_generate_and_save_recipes_happy_path(client, auth_header, monkeypatch):
    from src.interface.controllers import recipe_controller as ctrl
    from src.interface.serializers.recipe_serializers import RecipeSchema

    class FakePrepare:
        def execute(self, user_uid):
            return {"ingredients": ["egg", "potato"]}

    class FakeGenerate:
        def execute(self, structured_data):
            return {"generated_recipes": [
                {"title": "Tortilla", "duration": "15m", "difficulty": "Fácil", "ingredients": [], "steps": [], "category": "desayuno", "description": ""}
            ]}

    class FakeSave:
        def execute(self, user_uid, recipe_data):
            # Return a minimal object compatible with RecipeSchema
            class Obj(dict):
                pass
            obj = Obj()
            obj.update({
                "title": recipe_data["title"],
                "duration": recipe_data["duration"],
                "difficulty": recipe_data["difficulty"],
                "ingredients": [],
                "steps": [],
                "footer": "",
                "generated_by_ai": True,
                "saved_at": "2024-01-01T00:00:00Z",
                "category": "desayuno",
                "description": "",
                "image_path": None,
                "image_status": "generating",
                "generated_at": None,
            })
            return obj

    monkeypatch.setattr(ctrl, "make_prepare_recipe_generation_data_use_case", lambda: FakePrepare())
    monkeypatch.setattr(ctrl, "make_generate_recipes_use_case", lambda: FakeGenerate())
    monkeypatch.setattr(ctrl, "make_save_recipe_use_case", lambda: FakeSave())

    rv = client.post("/api/recipes/generate-save-from-inventory", headers=auth_header)
    assert rv.status_code == 200
    data = rv.get_json()
    assert "saved_recipes" in data
    assert data["saved_recipes"][0]["title"] == "Tortilla"

