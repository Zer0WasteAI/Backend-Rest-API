from datetime import datetime

from src.application.use_cases.recipes.save_recipe_use_case import SaveRecipeUseCase


class DummyRepo:
    def __init__(self):
        self.saved = []

    def exists_by_user_and_title(self, user_uid, title):
        # Always "exists" to validate duplicate check is relaxed
        return True

    def save(self, recipe):
        self.saved.append(recipe)


def test_save_recipe_does_not_block_duplicates_when_relaxed():
    repo = DummyRepo()
    use_case = SaveRecipeUseCase(repo)

    recipe_data = {
        "title": "Tortilla",
        "duration": "15m",
        "difficulty": "Fácil",
        "ingredients": [{"name": "Huevo", "quantity": 2, "type_unit": "u"}],
        "steps": [{"step_order": 1, "description": "Batir"}],
        "footer": "",
        "generated_by_ai": True,
        "category": "desayuno",
        "image_path": None,
        "description": "Simple tortilla"
    }

    # Should not raise even if repo says it "exists"
    result = use_case.execute("user-1", recipe_data)

    assert len(repo.saved) == 1
    assert result.title == "Tortilla"

