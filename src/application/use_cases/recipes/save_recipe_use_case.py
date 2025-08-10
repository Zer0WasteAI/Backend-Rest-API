import uuid
from datetime import datetime
from src.domain.models.recipe import Recipe
from src.shared.exceptions.custom import InvalidRequestDataException

class SaveRecipeUseCase:
    def __init__(self, recipe_repository):
        self.recipe_repository = recipe_repository

    def execute(self, user_uid: str, recipe_data: dict) -> Recipe:
        # Validar que no exista ya una receta con el mismo título para el usuario
        #if self.recipe_repository.exists_by_user_and_title(user_uid, recipe_data["title"]):
        #    raise InvalidRequestDataException("Ya tienes una receta guardada con este título")

        # Crear la receta
        recipe = Recipe(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            title=recipe_data["title"],
            duration=recipe_data["duration"],
            difficulty=recipe_data["difficulty"],
            ingredients=recipe_data["ingredients"],
            steps=recipe_data["steps"],
            footer=recipe_data.get("footer", ""),
            saved_at=datetime.now(),
            generated_by_ai=recipe_data.get("generated_by_ai", True),
            category=recipe_data.get("category", ""),
            image_path=recipe_data.get("", None),
            description=recipe_data.get("description", ""),
        )

        # Guardar en el repositorio
        self.recipe_repository.save(recipe)
        
        return recipe 