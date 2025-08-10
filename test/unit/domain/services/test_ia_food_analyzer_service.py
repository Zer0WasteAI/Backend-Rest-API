"""
Unit tests for IAFoodAnalyzerService abstract interface
Tests the contract and behavior expectations for AI food analyzer implementations
"""
import pytest
from abc import ABCMeta
from io import BytesIO
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, MagicMock

from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService


class TestIAFoodAnalyzerService:
    """Test suite for IAFoodAnalyzerService abstract interface"""
    
    def test_ia_food_analyzer_service_is_abstract(self):
        """Test that IAFoodAnalyzerService is an abstract base class"""
        # Act & Assert
        assert IAFoodAnalyzerService.__bases__ == (ABCMeta,)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            IAFoodAnalyzerService()
    
    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined"""
        # Arrange
        expected_methods = [
            'recognize_ingredients',
            'recognize_foods',
            'recognize_batch',
            'suggest_storage_type',
            'category_autotag', 
            'match_allergens',
            'generate_ingredient_image',
            'generate_food_image',
            'analyze_environmental_impact',
            'generate_utilization_ideas',
            'recognize_ingredients_complete'
        ]
        
        # Act & Assert
        abstract_methods = IAFoodAnalyzerService.__abstractmethods__
        for method_name in expected_methods:
            assert method_name in abstract_methods
            assert hasattr(IAFoodAnalyzerService, method_name)
    
    def test_method_signatures_and_documentation(self):
        """Test that methods have proper documentation"""
        # Test recognize_ingredients
        method = IAFoodAnalyzerService.recognize_ingredients
        assert method.__doc__ is not None
        assert "Analiza una imagen de ingredientes" in method.__doc__
        
        # Test recognize_foods
        method = IAFoodAnalyzerService.recognize_foods
        assert method.__doc__ is not None
        assert "Reconoce el plato de comida" in method.__doc__
        
        # Test generate_ingredient_image
        method = IAFoodAnalyzerService.generate_ingredient_image
        assert method.__doc__ is not None
        assert "Genera una imagen para un ingrediente" in method.__doc__
        assert "Args:" in method.__doc__
        assert "Returns:" in method.__doc__


class ConcreteIAFoodAnalyzerService(IAFoodAnalyzerService):
    """Concrete implementation for testing purposes"""
    
    def __init__(self):
        self.analysis_calls = []
        self.generated_images = []
    
    def recognize_ingredients(self, image_files: List) -> Dict[str, List[Dict[str, Any]]]:
        """Mock implementation for ingredient recognition"""
        self.analysis_calls.append({"method": "recognize_ingredients", "files": len(image_files)})
        
        ingredients = []
        for i, image_file in enumerate(image_files):
            ingredients.append({
                "name": f"Ingredient_{i+1}",
                "confidence": 0.95,
                "category": "Vegetable",
                "storage_type": "Refrigerator",
                "tips": f"Storage tips for ingredient {i+1}"
            })
        
        return {"ingredients": ingredients}
    
    def recognize_foods(self, image_files: List) -> Dict[str, List[Dict[str, Any]]]:
        """Mock implementation for food recognition"""
        self.analysis_calls.append({"method": "recognize_foods", "files": len(image_files)})
        
        foods = []
        for i, image_file in enumerate(image_files):
            foods.append({
                "name": f"Food_{i+1}",
                "confidence": 0.90,
                "category": "Main Dish",
                "calories": 350.0,
                "main_ingredients": [f"Ingredient_A_{i}", f"Ingredient_B_{i}"]
            })
        
        return {"foods": foods}
    
    def recognize_batch(self, image_files: List) -> Dict[str, List]:
        """Mock implementation for batch recognition"""
        self.analysis_calls.append({"method": "recognize_batch", "files": len(image_files)})
        
        results = []
        for i, image_file in enumerate(image_files):
            results.append({
                "image_index": i,
                "detected_items": [f"Item_{i}_A", f"Item_{i}_B"],
                "confidence_score": 0.85
            })
        
        return {"batch_results": results}
    
    def suggest_storage_type(self, food_name: str) -> str:
        """Mock implementation for storage suggestion"""
        self.analysis_calls.append({"method": "suggest_storage_type", "food": food_name})
        
        storage_map = {
            "banana": "Ambiente",
            "milk": "Refrigerado", 
            "ice_cream": "Congelado",
            "bread": "Ambiente"
        }
        return storage_map.get(food_name.lower(), "Refrigerado")
    
    def category_autotag(self, food_name: str) -> List[str]:
        """Mock implementation for category tagging"""
        self.analysis_calls.append({"method": "category_autotag", "food": food_name})
        
        category_map = {
            "apple": ["Fruta", "Dulce", "Natural"],
            "chicken": ["Proteína", "Carne", "Principal"],
            "carrot": ["Vegetal", "Naranja", "Crudo"]
        }
        return category_map.get(food_name.lower(), ["General", "Alimento"])
    
    def match_allergens(self, food_name: str, user_allergens: List[str]) -> List[str]:
        """Mock implementation for allergen matching"""
        self.analysis_calls.append({"method": "match_allergens", "food": food_name, "allergens": user_allergens})
        
        food_allergens = {
            "milk": ["lactose", "dairy"],
            "bread": ["gluten", "wheat"],
            "peanuts": ["nuts", "peanuts"]
        }
        
        found_allergens = []
        food_contains = food_allergens.get(food_name.lower(), [])
        for allergen in user_allergens:
            if allergen.lower() in food_contains:
                found_allergens.append(allergen)
        
        return found_allergens
    
    def generate_ingredient_image(self, ingredient_name: str, descripcion: str = "") -> Optional[BytesIO]:
        """Mock implementation for ingredient image generation"""
        self.analysis_calls.append({"method": "generate_ingredient_image", "ingredient": ingredient_name})
        
        # Simulate image generation
        if ingredient_name.lower() == "invalid":
            return None
        
        image_data = f"Generated image data for {ingredient_name}".encode()
        image_buffer = BytesIO(image_data)
        self.generated_images.append({"type": "ingredient", "name": ingredient_name})
        
        return image_buffer
    
    def generate_food_image(self, food_name: str, description: str = "", main_ingredients: List[str] = None) -> Optional[BytesIO]:
        """Mock implementation for food image generation"""
        self.analysis_calls.append({
            "method": "generate_food_image", 
            "food": food_name,
            "ingredients": main_ingredients or []
        })
        
        if food_name.lower() == "invalid":
            return None
        
        image_data = f"Generated food image for {food_name}".encode()
        image_buffer = BytesIO(image_data)
        self.generated_images.append({"type": "food", "name": food_name})
        
        return image_buffer
    
    def analyze_environmental_impact(self, ingredient_name: str) -> Dict[str, Any]:
        """Mock implementation for environmental impact analysis"""
        self.analysis_calls.append({"method": "analyze_environmental_impact", "ingredient": ingredient_name})
        
        impact_data = {
            "beef": {"co2": 60.0, "water": 15400, "severity": "high"},
            "apple": {"co2": 0.4, "water": 822, "severity": "low"},
            "rice": {"co2": 2.7, "water": 2497, "severity": "medium"}
        }
        
        data = impact_data.get(ingredient_name.lower(), {"co2": 5.0, "water": 1000, "severity": "medium"})
        
        return {
            "carbon_footprint": {"value": data["co2"], "unit": "kg CO2"},
            "water_footprint": {"value": data["water"], "unit": "liters"},
            "environmental_message": f"Impacto {data['severity']} para {ingredient_name}",
            "sustainability_score": 100 - (data["co2"] * 1.5)  # Simple calculation
        }
    
    def generate_utilization_ideas(self, ingredient_name: str, description: str = "") -> Dict[str, Any]:
        """Mock implementation for utilization ideas"""
        self.analysis_calls.append({"method": "generate_utilization_ideas", "ingredient": ingredient_name})
        
        return {
            "conservation_tips": [
                f"Conservar {ingredient_name} en lugar fresco",
                f"Usar {ingredient_name} antes de 7 días"
            ],
            "recipe_ideas": [
                f"Ensalada con {ingredient_name}",
                f"Sopa de {ingredient_name}"
            ],
            "preparation_methods": [
                "Crudo", "Cocido", "Al vapor"
            ],
            "waste_reduction": f"Aprovechar completamente el {ingredient_name}"
        }
    
    def recognize_ingredients_complete(self, image_files: List) -> Dict[str, List[Dict[str, Any]]]:
        """Mock implementation for complete ingredient recognition"""
        self.analysis_calls.append({"method": "recognize_ingredients_complete", "files": len(image_files)})
        
        complete_ingredients = []
        for i, image_file in enumerate(image_files):
            ingredient_name = f"CompleteIngredient_{i+1}"
            
            # Combine basic recognition with environmental and utilization data
            ingredient = {
                "name": ingredient_name,
                "confidence": 0.92,
                "category": "Complete Category",
                "storage_type": "Refrigerator",
                "environmental_impact": self.analyze_environmental_impact(ingredient_name),
                "utilization_ideas": self.generate_utilization_ideas(ingredient_name)
            }
            complete_ingredients.append(ingredient)
        
        return {"complete_ingredients": complete_ingredients}


class TestConcreteIAFoodAnalyzerService:
    """Test suite for concrete IAFoodAnalyzerService implementation"""
    
    @pytest.fixture
    def analyzer_service(self):
        """Concrete analyzer service for testing"""
        return ConcreteIAFoodAnalyzerService()
    
    @pytest.fixture
    def sample_image_files(self):
        """Sample image files for testing"""
        return [
            Mock(name="image1.jpg"),
            Mock(name="image2.jpg"),
            Mock(name="image3.jpg")
        ]
    
    def test_recognize_ingredients(self, analyzer_service, sample_image_files):
        """Test ingredient recognition functionality"""
        # Act
        result = analyzer_service.recognize_ingredients(sample_image_files)
        
        # Assert
        assert "ingredients" in result
        assert len(result["ingredients"]) == 3
        
        for i, ingredient in enumerate(result["ingredients"]):
            assert ingredient["name"] == f"Ingredient_{i+1}"
            assert ingredient["confidence"] == 0.95
            assert ingredient["category"] == "Vegetable"
            assert "storage_type" in ingredient
        
        # Verify method was called and logged
        assert len(analyzer_service.analysis_calls) == 1
        assert analyzer_service.analysis_calls[0]["method"] == "recognize_ingredients"
        assert analyzer_service.analysis_calls[0]["files"] == 3
    
    def test_recognize_foods(self, analyzer_service, sample_image_files):
        """Test food recognition functionality"""
        # Act
        result = analyzer_service.recognize_foods(sample_image_files)
        
        # Assert
        assert "foods" in result
        assert len(result["foods"]) == 3
        
        for i, food in enumerate(result["foods"]):
            assert food["name"] == f"Food_{i+1}"
            assert food["confidence"] == 0.90
            assert food["calories"] == 350.0
            assert len(food["main_ingredients"]) == 2
    
    def test_recognize_batch(self, analyzer_service, sample_image_files):
        """Test batch recognition functionality"""
        # Act
        result = analyzer_service.recognize_batch(sample_image_files)
        
        # Assert
        assert "batch_results" in result
        assert len(result["batch_results"]) == 3
        
        for i, batch_result in enumerate(result["batch_results"]):
            assert batch_result["image_index"] == i
            assert len(batch_result["detected_items"]) == 2
            assert batch_result["confidence_score"] == 0.85
    
    @pytest.mark.parametrize("food_name,expected_storage", [
        ("banana", "Ambiente"),
        ("milk", "Refrigerado"),
        ("ice_cream", "Congelado"),
        ("bread", "Ambiente"),
        ("unknown_food", "Refrigerado"),  # Default case
    ])
    def test_suggest_storage_type(self, analyzer_service, food_name, expected_storage):
        """Test storage type suggestion for various foods"""
        # Act
        result = analyzer_service.suggest_storage_type(food_name)
        
        # Assert
        assert result == expected_storage
    
    @pytest.mark.parametrize("food_name,expected_categories", [
        ("apple", ["Fruta", "Dulce", "Natural"]),
        ("chicken", ["Proteína", "Carne", "Principal"]),
        ("carrot", ["Vegetal", "Naranja", "Crudo"]),
        ("unknown", ["General", "Alimento"]),  # Default case
    ])
    def test_category_autotag(self, analyzer_service, food_name, expected_categories):
        """Test category auto-tagging for various foods"""
        # Act
        result = analyzer_service.category_autotag(food_name)
        
        # Assert
        assert result == expected_categories
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_match_allergens_with_matches(self, analyzer_service):
        """Test allergen matching when allergens are found"""
        # Arrange
        food_name = "milk"
        user_allergens = ["lactose", "nuts", "gluten"]
        
        # Act
        result = analyzer_service.match_allergens(food_name, user_allergens)
        
        # Assert
        assert "lactose" in result
        assert "nuts" not in result  # Milk doesn't contain nuts
        assert "gluten" not in result  # Milk doesn't contain gluten
        assert len(result) == 1
    
    def test_match_allergens_no_matches(self, analyzer_service):
        """Test allergen matching when no allergens are found"""
        # Arrange
        food_name = "apple"  # Not in our allergen map
        user_allergens = ["lactose", "nuts", "gluten"]
        
        # Act
        result = analyzer_service.match_allergens(food_name, user_allergens)
        
        # Assert
        assert result == []
    
    def test_generate_ingredient_image_success(self, analyzer_service):
        """Test successful ingredient image generation"""
        # Arrange
        ingredient_name = "tomato"
        description = "Fresh red tomato"
        
        # Act
        result = analyzer_service.generate_ingredient_image(ingredient_name, description)
        
        # Assert
        assert result is not None
        assert isinstance(result, BytesIO)
        
        # Check content
        image_content = result.getvalue().decode()
        assert ingredient_name in image_content
        
        # Verify tracking
        assert len(analyzer_service.generated_images) == 1
        assert analyzer_service.generated_images[0]["type"] == "ingredient"
        assert analyzer_service.generated_images[0]["name"] == ingredient_name
    
    def test_generate_ingredient_image_failure(self, analyzer_service):
        """Test ingredient image generation failure"""
        # Act
        result = analyzer_service.generate_ingredient_image("invalid")
        
        # Assert
        assert result is None
    
    def test_generate_food_image_success(self, analyzer_service):
        """Test successful food image generation"""
        # Arrange
        food_name = "pizza"
        description = "Delicious homemade pizza"
        main_ingredients = ["tomato", "cheese", "dough"]
        
        # Act
        result = analyzer_service.generate_food_image(food_name, description, main_ingredients)
        
        # Assert
        assert result is not None
        assert isinstance(result, BytesIO)
        
        # Check tracking
        assert len(analyzer_service.generated_images) == 1
        assert analyzer_service.generated_images[0]["type"] == "food"
    
    def test_analyze_environmental_impact(self, analyzer_service):
        """Test environmental impact analysis"""
        # Arrange
        ingredient_name = "beef"
        
        # Act
        result = analyzer_service.analyze_environmental_impact(ingredient_name)
        
        # Assert
        assert "carbon_footprint" in result
        assert "water_footprint" in result
        assert "environmental_message" in result
        assert "sustainability_score" in result
        
        assert result["carbon_footprint"]["value"] == 60.0
        assert result["carbon_footprint"]["unit"] == "kg CO2"
        assert result["water_footprint"]["value"] == 15400
        assert result["water_footprint"]["unit"] == "liters"
    
    def test_generate_utilization_ideas(self, analyzer_service):
        """Test utilization ideas generation"""
        # Arrange
        ingredient_name = "carrot"
        
        # Act
        result = analyzer_service.generate_utilization_ideas(ingredient_name)
        
        # Assert
        assert "conservation_tips" in result
        assert "recipe_ideas" in result
        assert "preparation_methods" in result
        assert "waste_reduction" in result
        
        assert isinstance(result["conservation_tips"], list)
        assert isinstance(result["recipe_ideas"], list)
        assert len(result["conservation_tips"]) > 0
        assert len(result["recipe_ideas"]) > 0
    
    def test_recognize_ingredients_complete(self, analyzer_service, sample_image_files):
        """Test complete ingredient recognition with all features"""
        # Act
        result = analyzer_service.recognize_ingredients_complete(sample_image_files)
        
        # Assert
        assert "complete_ingredients" in result
        assert len(result["complete_ingredients"]) == 3
        
        for ingredient in result["complete_ingredients"]:
            assert "name" in ingredient
            assert "confidence" in ingredient
            assert "environmental_impact" in ingredient
            assert "utilization_ideas" in ingredient
            
            # Check nested structures
            env_impact = ingredient["environmental_impact"]
            assert "carbon_footprint" in env_impact
            assert "water_footprint" in env_impact
            
            util_ideas = ingredient["utilization_ideas"]
            assert "conservation_tips" in util_ideas
            assert "recipe_ideas" in util_ideas
    
    def test_multiple_method_calls_tracking(self, analyzer_service):
        """Test that multiple method calls are properly tracked"""
        # Arrange & Act
        analyzer_service.suggest_storage_type("banana")
        analyzer_service.category_autotag("apple")
        analyzer_service.analyze_environmental_impact("beef")
        
        # Assert
        assert len(analyzer_service.analysis_calls) == 3
        methods_called = [call["method"] for call in analyzer_service.analysis_calls]
        assert "suggest_storage_type" in methods_called
        assert "category_autotag" in methods_called
        assert "analyze_environmental_impact" in methods_called