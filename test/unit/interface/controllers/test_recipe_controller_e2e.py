from flask import Flask
from flask_jwt_extended import create_access_token


class _StubPrepareDataUC:
    def execute(self, user_uid: str):
        return {"ingredients": [{"name": "Tomates", "qty": 1}]}


class _StubGenerateRecipesUC:
    def execute(self, structured_data: dict):
        return {
            "generated_recipes": [
                {
                    "name": "Ensalada",
                    "ingredients": [
                        {"name": "Tomates", "quantity": 1, "unit": "u"}
                    ],
                    "steps": ["Cortar", "Servir"],
                }
            ],
            "generation_summary": {"total_recipes": 1}
        }


def test_generate_recipes_from_inventory(monkeypatch, app: Flask, client):
    # Stub out use case factories
    monkeypatch.setattr(
        "src.application.factories.recipe_usecase_factory.make_prepare_recipe_generation_data_use_case",
        lambda: _StubPrepareDataUC(),
        raising=True,
    )
    monkeypatch.setattr(
        "src.application.factories.recipe_usecase_factory.make_generate_recipes_use_case",
        lambda: _StubGenerateRecipesUC(),
        raising=True,
    )

    with app.app_context():
        token = create_access_token(identity="u1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/recipes/generate-from-inventory", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["generation_summary"]["total_recipes"] == 1
    assert data["generated_recipes"][0]["name"] == "Ensalada"

