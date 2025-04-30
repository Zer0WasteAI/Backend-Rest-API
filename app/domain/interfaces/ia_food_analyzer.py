from abc import ABC, abstractmethod
from typing import List, Dict

class IAFoodAnalyzer(ABC):
    @abstractmethod
    def recognize_ingredients(self, image_file) -> List[Dict]:
        """
        Analiza una imagen de ingredientes y devuelve metadatos.
        """
        pass

    @abstractmethod
    def recognize_food(self, image_file) -> List[Dict]:
        """
        Reconoce el plato de comida en una imagen y devuelve metadatos.
        """
        pass

    @abstractmethod
    def recognize_batch(self, image_files: List) -> List[Dict]:
        """
        Analiza varias imágenes y devuelve una lista de resultados estructurados.
        """
        pass

    @abstractmethod
    def suggest_storage_type(self, food_name: str) -> str:
        """
        Sugiere el tipo de almacenamiento óptimo (Ej: Refrigerado, Ambiente, Congelado).
        """
        pass

    @abstractmethod
    def category_autotag(self, food_name: str) -> List[str]:
        """
        Sugiere etiquetas de categoría para un alimento o ingrediente (Ej: Fruta, Vegetal, Proteína).
        """
        pass

    @abstractmethod
    def match_allergens(self, food_name: str, user_allergens: List[str]) -> List[str]:
        """
        Detecta si un alimento contiene alérgenos que coinciden con una lista de alérgenos del usuario.
        """
        pass