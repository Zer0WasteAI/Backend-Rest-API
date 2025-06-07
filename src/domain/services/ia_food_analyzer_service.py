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
    def generate_ingredient_image(self, ingredient_name: str, descripcion: str = "") -> Optional[BytesIO]:
        """
        Genera una imagen para un ingrediente usando AI.
        
        Args:
            ingredient_name: Nombre del ingrediente
            descripcion: Descripción de las características del ingrediente
            
        Returns:
            BytesIO object con los datos de la imagen generada, o None si falla
        """
        pass

    @abstractmethod
    def analyze_environmental_impact(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Analiza el impacto ambiental de un ingrediente específico.
        
        Args:
            ingredient_name: Nombre del ingrediente a analizar
            
        Returns:
            Diccionario con información del impacto ambiental (CO2, agua, mensaje)
        """
        pass

    @abstractmethod
    def generate_utilization_ideas(self, ingredient_name: str, description: str = "") -> Dict[str, Any]:
        """
        Genera ideas de aprovechamiento para un ingrediente específico.
        
        Args:
            ingredient_name: Nombre del ingrediente
            description: Descripción del ingrediente
            
        Returns:
            Diccionario con ideas de aprovechamiento y conservación
        """
        pass

    @abstractmethod
    def recognize_ingredients_complete(self, image_files: List) -> Dict[str, List[Dict[str, Any]]]:
        """
        Reconoce ingredientes con información completa: básica + impacto ambiental + aprovechamiento.
        
        Args:
            image_files: Lista de archivos de imagen
            
        Returns:
            Diccionario con ingredientes enriquecidos con toda la información
        """
        pass