from typing import Dict, Any

class GenerateRecipesUseCase:
    def __init__(self, recipe_service):
        self.recipe_service = recipe_service

    def execute(self, generation_data: Dict[str, Any], num_recipes: int = 2) -> Dict[str, Any]:
        return self.recipe_service.generate_recipes(generation_data, num_recipes)

