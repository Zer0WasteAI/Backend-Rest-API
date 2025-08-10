"""
Unit tests for IARecipeGeneratorService abstract interface
Tests the contract and behavior expectations for AI recipe generator implementations
"""
import pytest
from abc import ABCMeta
from typing import Dict, Any
from unittest.mock import Mock

from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService


class TestIARecipeGeneratorService:
    """Test suite for IARecipeGeneratorService abstract interface"""
    
    def test_ia_recipe_generator_service_is_abstract(self):
        """Test that IARecipeGeneratorService is an abstract base class"""
        # Act & Assert
        assert IARecipeGeneratorService.__bases__ == (ABCMeta,)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            IARecipeGeneratorService()
    
    def test_generate_recipes_is_abstract_method(self):
        """Test that generate_recipes is defined as abstract method"""
        # Arrange
        abstract_methods = IARecipeGeneratorService.__abstractmethods__
        
        # Assert
        assert 'generate_recipes' in abstract_methods
    
    def test_generate_recipes_signature_and_documentation(self):
        """Test generate_recipes method signature and documentation"""
        # Arrange
        method = IARecipeGeneratorService.generate_recipes
        
        # Assert
        assert hasattr(IARecipeGeneratorService, 'generate_recipes')
        assert method.__doc__ is not None
        assert 'Genera recetas en base a los ingredientes' in method.__doc__


class ConcreteIARecipeGeneratorService(IARecipeGeneratorService):
    """Concrete implementation for testing purposes"""
    
    def __init__(self):
        self.generation_history = []
        self.recipes_database = {
            "italian": [
                {
                    "title": "Pasta Primavera",
                    "duration": "25 minutes", 
                    "difficulty": "Fácil",
                    "ingredients": ["pasta", "vegetables", "olive oil"],
                    "steps": ["Boil pasta", "Sauté vegetables", "Combine"]
                },
                {
                    "title": "Risotto de Hongos",
                    "duration": "35 minutes",
                    "difficulty": "Medio", 
                    "ingredients": ["rice", "mushrooms", "broth"],
                    "steps": ["Prepare broth", "Cook rice", "Add mushrooms"]
                }
            ],
            "mexican": [
                {
                    "title": "Tacos de Vegetales",
                    "duration": "20 minutes",
                    "difficulty": "Fácil",
                    "ingredients": ["tortillas", "beans", "vegetables"],
                    "steps": ["Warm tortillas", "Prepare filling", "Assemble"]
                }
            ],
            "asian": [
                {
                    "title": "Stir Fry de Vegetales",
                    "duration": "15 minutes",
                    "difficulty": "Fácil", 
                    "ingredients": ["vegetables", "soy sauce", "ginger"],
                    "steps": ["Heat wok", "Add vegetables", "Season"]
                }
            ]
        }
    
    def generate_recipes(self, data: Dict[str, Any], num_recipes: int, recipe_categories: list) -> Dict[str, Any]:
        """Mock implementation for recipe generation"""
        # Log the generation request
        self.generation_history.append({
            "data": data,
            "num_recipes": num_recipes,
            "categories": recipe_categories
        })
        
        # Extract available ingredients from data
        available_ingredients = data.get("available_ingredients", [])
        user_preferences = data.get("preferences", {})
        dietary_restrictions = data.get("dietary_restrictions", [])
        
        # Generate recipes based on categories
        generated_recipes = []
        for category in recipe_categories:
            if category.lower() in self.recipes_database:
                category_recipes = self.recipes_database[category.lower()]
                for recipe in category_recipes[:num_recipes]:
                    # Modify recipe based on available ingredients
                    modified_recipe = recipe.copy()
                    
                    # Check ingredient availability
                    available_count = sum(1 for ing in recipe["ingredients"] 
                                        if any(av_ing.lower() in ing.lower() 
                                             for av_ing in available_ingredients))
                    
                    modified_recipe.update({
                        "category": category,
                        "ingredient_match_score": available_count / len(recipe["ingredients"]),
                        "can_make": available_count >= len(recipe["ingredients"]) * 0.7,  # 70% match
                        "missing_ingredients": [ing for ing in recipe["ingredients"] 
                                              if not any(av_ing.lower() in ing.lower() 
                                                       for av_ing in available_ingredients)],
                        "user_rating": user_preferences.get("rating", 4.0),
                        "dietary_compliant": len(set(recipe["ingredients"]) & set(dietary_restrictions)) == 0
                    })
                    
                    generated_recipes.append(modified_recipe)
                    
                    if len(generated_recipes) >= num_recipes:
                        break
                        
                if len(generated_recipes) >= num_recipes:
                    break
        
        # If not enough recipes found, generate generic ones
        while len(generated_recipes) < num_recipes:
            generic_recipe = {
                "title": f"Receta Generica {len(generated_recipes) + 1}",
                "duration": "30 minutes",
                "difficulty": "Medio",
                "category": "General",
                "ingredients": available_ingredients[:3] if available_ingredients else ["ingredient1", "ingredient2"],
                "steps": ["Step 1", "Step 2", "Step 3"],
                "ingredient_match_score": 1.0 if available_ingredients else 0.0,
                "can_make": bool(available_ingredients),
                "missing_ingredients": [],
                "user_rating": 3.5,
                "dietary_compliant": True
            }
            generated_recipes.append(generic_recipe)
        
        return {
            "recipes": generated_recipes,
            "total_generated": len(generated_recipes),
            "generation_metadata": {
                "categories_requested": recipe_categories,
                "ingredients_analyzed": len(available_ingredients),
                "preferences_applied": bool(user_preferences),
                "dietary_restrictions_count": len(dietary_restrictions)
            }
        }


class TestConcreteIARecipeGeneratorService:
    """Test suite for concrete IARecipeGeneratorService implementation"""
    
    @pytest.fixture
    def recipe_service(self):
        """Concrete recipe generator service for testing"""
        return ConcreteIARecipeGeneratorService()
    
    @pytest.fixture
    def sample_recipe_data(self):
        """Sample data for recipe generation"""
        return {
            "available_ingredients": ["pasta", "tomatoes", "cheese", "basil"],
            "preferences": {
                "cuisine": "italian",
                "difficulty": "easy",
                "max_time": 30,
                "rating": 4.5
            },
            "dietary_restrictions": ["gluten"],
            "user_id": "test-user-123"
        }
    
    def test_concrete_implementation_can_be_instantiated(self, recipe_service):
        """Test that concrete implementation can be created"""
        # Assert
        assert isinstance(recipe_service, IARecipeGeneratorService)
        assert isinstance(recipe_service, ConcreteIARecipeGeneratorService)
        assert len(recipe_service.generation_history) == 0
    
    def test_generate_recipes_basic_functionality(self, recipe_service, sample_recipe_data):
        """Test basic recipe generation functionality"""
        # Arrange
        num_recipes = 2
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        assert isinstance(result, dict)
        assert "recipes" in result
        assert "total_generated" in result
        assert "generation_metadata" in result
        
        assert len(result["recipes"]) == num_recipes
        assert result["total_generated"] == num_recipes
        
        # Verify generation was logged
        assert len(recipe_service.generation_history) == 1
        assert recipe_service.generation_history[0]["num_recipes"] == num_recipes
        assert recipe_service.generation_history[0]["categories"] == categories
    
    def test_generate_recipes_with_ingredient_matching(self, recipe_service, sample_recipe_data):
        """Test recipe generation with ingredient matching logic"""
        # Arrange
        num_recipes = 1
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        recipe = result["recipes"][0]
        assert "ingredient_match_score" in recipe
        assert "can_make" in recipe
        assert "missing_ingredients" in recipe
        
        # Should have some ingredient matches since we provided pasta
        assert recipe["ingredient_match_score"] > 0
        assert isinstance(recipe["missing_ingredients"], list)
    
    def test_generate_recipes_multiple_categories(self, recipe_service, sample_recipe_data):
        """Test recipe generation with multiple categories"""
        # Arrange
        num_recipes = 3
        categories = ["italian", "mexican", "asian"]
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        assert len(result["recipes"]) == num_recipes
        
        # Check that different categories are represented
        recipe_categories = [recipe.get("category") for recipe in result["recipes"]]
        assert len(set(recipe_categories)) > 1  # Should have multiple categories
        
        # Verify metadata
        metadata = result["generation_metadata"]
        assert metadata["categories_requested"] == categories
        assert metadata["ingredients_analyzed"] == len(sample_recipe_data["available_ingredients"])
    
    def test_generate_recipes_with_no_available_ingredients(self, recipe_service):
        """Test recipe generation when no ingredients are available"""
        # Arrange
        empty_data = {
            "available_ingredients": [],
            "preferences": {},
            "dietary_restrictions": []
        }
        num_recipes = 2
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(empty_data, num_recipes, categories)
        
        # Assert
        assert len(result["recipes"]) == num_recipes
        
        # Should generate generic recipes when no ingredients available
        for recipe in result["recipes"]:
            assert recipe["ingredient_match_score"] >= 0
            assert "can_make" in recipe
    
    def test_generate_recipes_with_unknown_category(self, recipe_service, sample_recipe_data):
        """Test recipe generation with unknown category"""
        # Arrange
        num_recipes = 2
        categories = ["unknown_cuisine"]
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        assert len(result["recipes"]) == num_recipes
        
        # Should generate generic recipes for unknown categories
        for recipe in result["recipes"]:
            assert recipe["title"].startswith("Receta Generica")
            assert recipe["category"] == "General"
    
    @pytest.mark.parametrize("num_recipes,expected_count", [
        (1, 1),
        (3, 3),
        (5, 5),
        (0, 0),
    ])
    def test_generate_recipes_different_quantities(self, recipe_service, sample_recipe_data, num_recipes, expected_count):
        """Test recipe generation with different quantities"""
        # Arrange
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        assert len(result["recipes"]) == expected_count
        assert result["total_generated"] == expected_count
    
    def test_generate_recipes_dietary_restrictions_compliance(self, recipe_service):
        """Test that dietary restrictions are considered"""
        # Arrange
        data = {
            "available_ingredients": ["pasta", "cheese"],
            "preferences": {},
            "dietary_restrictions": ["pasta"]  # User can't eat pasta
        }
        num_recipes = 1
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(data, num_recipes, categories)
        
        # Assert
        recipe = result["recipes"][0]
        assert "dietary_compliant" in recipe
        # The compliance logic checks if dietary restrictions intersect with ingredients
    
    def test_generate_recipes_user_preferences_applied(self, recipe_service):
        """Test that user preferences are applied to recipes"""
        # Arrange
        data = {
            "available_ingredients": ["pasta"],
            "preferences": {
                "rating": 4.8,
                "cuisine": "italian"
            },
            "dietary_restrictions": []
        }
        num_recipes = 1
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(data, num_recipes, categories)
        
        # Assert
        recipe = result["recipes"][0]
        assert recipe["user_rating"] == 4.8
        
        # Verify metadata shows preferences were applied
        metadata = result["generation_metadata"]
        assert metadata["preferences_applied"] is True
    
    def test_generation_history_tracking(self, recipe_service, sample_recipe_data):
        """Test that generation history is properly tracked"""
        # Arrange
        categories1 = ["italian"]
        categories2 = ["mexican"]
        
        # Act
        recipe_service.generate_recipes(sample_recipe_data, 1, categories1)
        recipe_service.generate_recipes(sample_recipe_data, 2, categories2)
        
        # Assert
        assert len(recipe_service.generation_history) == 2
        
        # Check first call
        first_call = recipe_service.generation_history[0]
        assert first_call["num_recipes"] == 1
        assert first_call["categories"] == categories1
        
        # Check second call  
        second_call = recipe_service.generation_history[1]
        assert second_call["num_recipes"] == 2
        assert second_call["categories"] == categories2
    
    def test_recipe_structure_completeness(self, recipe_service, sample_recipe_data):
        """Test that generated recipes have all required fields"""
        # Arrange
        num_recipes = 1
        categories = ["italian"]
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        recipe = result["recipes"][0]
        
        # Check required recipe fields
        required_fields = [
            "title", "duration", "difficulty", "ingredients", "steps",
            "category", "ingredient_match_score", "can_make", 
            "missing_ingredients", "user_rating", "dietary_compliant"
        ]
        
        for field in required_fields:
            assert field in recipe, f"Recipe missing required field: {field}"
        
        # Check field types
        assert isinstance(recipe["title"], str)
        assert isinstance(recipe["ingredients"], list)
        assert isinstance(recipe["steps"], list)
        assert isinstance(recipe["ingredient_match_score"], (int, float))
        assert isinstance(recipe["can_make"], bool)
        assert isinstance(recipe["missing_ingredients"], list)
    
    def test_empty_categories_list(self, recipe_service, sample_recipe_data):
        """Test recipe generation with empty categories list"""
        # Arrange
        num_recipes = 1
        categories = []
        
        # Act
        result = recipe_service.generate_recipes(sample_recipe_data, num_recipes, categories)
        
        # Assert
        assert len(result["recipes"]) == num_recipes
        # Should generate generic recipes when no categories specified
        assert result["recipes"][0]["category"] == "General"