from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from io import BytesIO

class IAFoodAnalyzerService(ABC):
    @abstractmethod
    def recognize_ingredients(self, image_files: List) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analiza una imagen de ingredientes y devuelve metadatos.
        """
        pass

    @abstractmethod
    def recognize_foods(self, image_files: List) -> Dict[str, List[Dict[str, Any]]]:
        """
        Reconoce el plato de comida en una imagen y devuelve metadatos.
        """
        pass

    @abstractmethod
    def recognize_batch(self, image_files: List) -> Dict[str, List]:
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

    @abstractmethod
    def generate_ingredient_image(self, ingredient_name: str) -> Optional[BytesIO]:
        """
        Genera una imagen para un ingrediente usando AI.
        
        Args:
            ingredient_name: Nombre del ingrediente
            
        Returns:
            BytesIO object con los datos de la imagen generada, o None si falla
        """
        pass