from abc import ABC, abstractmethod
from typing import Dict, Any

class IARecipeGeneratorService(ABC):
    @abstractmethod
    def generate_recipes(self, data: Dict[str, Any], num_recipes, recipe_categories) -> Dict[str, Any]:
        """
        Genera recetas en base a los ingredientes disponibles, prioridades y preferencias.
        """
        pass
