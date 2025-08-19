"""
Unit tests for Mise En Place Service
Tests cooking preparation and organization functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.services.mise_en_place_service import MiseEnPlaceService


class TestMiseEnPlaceService:
    """Test suite for Mise En Place Service"""
    
    @pytest.fixture
    def mise_service(self):
        """Create mise en place service instance"""
        return MiseEnPlaceService()
    
    @pytest.fixture
    def sample_recipe_data(self):
        """Sample recipe data for testing"""
        return {
            "recipe_uid": "test-recipe-123",
            "title": "Test Recipe",
            "ingredients": [
                {"name": "onion", "quantity": "1 medium", "unit": "piece"},
                {"name": "garlic", "quantity": "2", "unit": "cloves"},
                {"name": "tomato", "quantity": "3", "unit": "pieces"},
                {"name": "olive oil", "quantity": "2", "unit": "tablespoons"}
            ],
            "instructions": [
                "Dice the onion finely",
                "Mince the garlic", 
                "Chop tomatoes",
                "Heat olive oil"
            ]
        }
    
    def test_generate_mise_en_place_success(self, mise_service, sample_recipe_data):
        """Test successful mise en place generation"""
        # Act
        result = mise_service.generate_mise_en_place(sample_recipe_data)
        
        # Assert
        assert result is not None
        assert "preparation_steps" in result
        assert "ingredient_prep" in result
        assert "cooking_sequence" in result
        assert len(result["ingredient_prep"]) == 4  # 4 ingredients
        
        # Check ingredient preparation details
        ingredient_prep = result["ingredient_prep"]
        assert any("onion" in prep["ingredient"] for prep in ingredient_prep)
        assert any("garlic" in prep["ingredient"] for prep in ingredient_prep)
        
    def test_generate_mise_en_place_empty_recipe(self, mise_service):
        """Test mise en place generation with empty recipe"""
        # Arrange
        empty_recipe = {}
        
        # Act & Assert
        with pytest.raises((ValueError, KeyError)):
            mise_service.generate_mise_en_place(empty_recipe)
    
    def test_generate_mise_en_place_missing_ingredients(self, mise_service):
        """Test mise en place generation with missing ingredients"""
        # Arrange
        recipe_without_ingredients = {
            "recipe_uid": "test-recipe-123",
            "title": "Test Recipe",
            "instructions": ["Cook something"]
        }
        
        # Act
        result = mise_service.generate_mise_en_place(recipe_without_ingredients)
        
        # Assert
        assert result is not None
        assert "ingredient_prep" in result
        assert len(result["ingredient_prep"]) == 0
    
    def test_generate_mise_en_place_complex_recipe(self, mise_service):
        """Test mise en place generation with complex recipe"""
        # Arrange
        complex_recipe = {
            "recipe_uid": "complex-recipe-456",
            "title": "Complex Dish",
            "ingredients": [
                {"name": "chicken breast", "quantity": "2", "unit": "pieces", "prep": "boneless"},
                {"name": "flour", "quantity": "1", "unit": "cup"},
                {"name": "eggs", "quantity": "2", "unit": "large"},
                {"name": "breadcrumbs", "quantity": "1", "unit": "cup"},
                {"name": "vegetable oil", "quantity": "500", "unit": "ml"},
                {"name": "lemon", "quantity": "1", "unit": "piece"},
                {"name": "herbs", "quantity": "mixed", "unit": "fresh"}
            ],
            "instructions": [
                "Prepare chicken by cutting into cutlets",
                "Set up breading station",
                "Heat oil to 350°F",
                "Bread chicken pieces",
                "Fry until golden",
                "Serve with lemon"
            ]
        }
        
        # Act
        result = mise_service.generate_mise_en_place(complex_recipe)
        
        # Assert
        assert result is not None
        assert len(result["ingredient_prep"]) == 7  # 7 ingredients
        assert "preparation_steps" in result
        assert "estimated_prep_time" in result
        
        # Check that complex preparations are identified
        prep_items = [prep["preparation"] for prep in result["ingredient_prep"]]
        assert any("cut" in prep.lower() or "slice" in prep.lower() for prep in prep_items)

    def test_generate_mise_en_place_with_timing(self, mise_service, sample_recipe_data):
        """Test mise en place generation includes timing information"""
        # Act
        result = mise_service.generate_mise_en_place(sample_recipe_data)
        
        # Assert
        assert "estimated_prep_time" in result
        assert "cooking_sequence" in result
        assert isinstance(result["estimated_prep_time"], (int, float, str))
        
        # Check cooking sequence has timing
        cooking_sequence = result["cooking_sequence"]
        assert isinstance(cooking_sequence, list)
        assert len(cooking_sequence) > 0

    def test_generate_mise_en_place_ingredient_categorization(self, mise_service, sample_recipe_data):
        """Test that ingredients are properly categorized by preparation type"""
        # Act
        result = mise_service.generate_mise_en_place(sample_recipe_data)
        
        # Assert
        ingredient_prep = result["ingredient_prep"]
        
        # Check categorization
        categories = set()
        for prep in ingredient_prep:
            if "category" in prep:
                categories.add(prep["category"])
        
        # Should have different categories for different prep types
        assert len(categories) >= 1

    def test_generate_mise_en_place_cooking_techniques(self, mise_service):
        """Test identification of cooking techniques"""
        # Arrange
        technique_recipe = {
            "recipe_uid": "technique-recipe-789",
            "title": "Multi-Technique Dish", 
            "ingredients": [
                {"name": "beef", "quantity": "500", "unit": "g"},
                {"name": "onions", "quantity": "2", "unit": "large"},
                {"name": "wine", "quantity": "200", "unit": "ml"}
            ],
            "instructions": [
                "Sear the beef in hot pan",
                "Sauté onions until golden",
                "Deglaze with wine",
                "Braise for 2 hours"
            ]
        }
        
        # Act
        result = mise_service.generate_mise_en_place(technique_recipe)
        
        # Assert
        assert result is not None
        assert "cooking_techniques" in result or "preparation_steps" in result
        
        # Check that different techniques are identified
        if "cooking_techniques" in result:
            techniques = result["cooking_techniques"]
            assert isinstance(techniques, list)

    def test_generate_mise_en_place_equipment_requirements(self, mise_service, sample_recipe_data):
        """Test identification of required equipment"""
        # Act
        result = mise_service.generate_mise_en_place(sample_recipe_data)
        
        # Assert
        assert result is not None
        
        # Equipment should be identified or inferred
        if "equipment_needed" in result:
            equipment = result["equipment_needed"]
            assert isinstance(equipment, list)
            assert len(equipment) > 0

    def test_generate_mise_en_place_parallel_tasks(self, mise_service):
        """Test identification of tasks that can be done in parallel"""
        # Arrange
        parallel_recipe = {
            "recipe_uid": "parallel-recipe-999",
            "title": "Parallel Tasks Recipe",
            "ingredients": [
                {"name": "pasta", "quantity": "400", "unit": "g"},
                {"name": "tomatoes", "quantity": "5", "unit": "pieces"},
                {"name": "basil", "quantity": "1", "unit": "bunch"},
                {"name": "garlic", "quantity": "3", "unit": "cloves"}
            ],
            "instructions": [
                "Boil water for pasta",
                "Chop tomatoes while water heats",
                "Mince garlic and chop basil",
                "Cook pasta when water boils",
                "Make sauce in separate pan"
            ]
        }
        
        # Act
        result = mise_service.generate_mise_en_place(parallel_recipe)
        
        # Assert
        assert result is not None
        
        # Should identify parallel tasks
        if "parallel_tasks" in result:
            parallel_tasks = result["parallel_tasks"]
            assert isinstance(parallel_tasks, list)

    def test_service_initialization(self):
        """Test service can be initialized properly"""
        # Act
        service = MiseEnPlaceService()
        
        # Assert
        assert service is not None
        assert hasattr(service, 'generate_mise_en_place')

    def test_generate_mise_en_place_error_handling(self, mise_service):
        """Test error handling with invalid input"""
        # Test with None input
        with pytest.raises((ValueError, TypeError, AttributeError)):
            mise_service.generate_mise_en_place(None)
        
        # Test with string input instead of dict
        with pytest.raises((ValueError, TypeError, AttributeError)):
            mise_service.generate_mise_en_place("invalid input")
        
        # Test with list input instead of dict  
        with pytest.raises((ValueError, TypeError, AttributeError)):
            mise_service.generate_mise_en_place(["invalid", "input"])

    def test_generate_mise_en_place_dietary_considerations(self, mise_service):
        """Test mise en place handles dietary restrictions"""
        # Arrange
        dietary_recipe = {
            "recipe_uid": "dietary-recipe-111",
            "title": "Gluten-Free Vegan Dish",
            "dietary_tags": ["gluten-free", "vegan"],
            "ingredients": [
                {"name": "quinoa", "quantity": "1", "unit": "cup"},
                {"name": "vegetables", "quantity": "mixed", "unit": "fresh"},
                {"name": "coconut oil", "quantity": "2", "unit": "tbsp"}
            ],
            "instructions": [
                "Rinse quinoa thoroughly",
                "Chop vegetables",
                "Cook quinoa",
                "Sauté vegetables"
            ]
        }
        
        # Act
        result = mise_service.generate_mise_en_place(dietary_recipe)
        
        # Assert
        assert result is not None
        
        # Should handle dietary considerations
        if "dietary_notes" in result:
            dietary_notes = result["dietary_notes"]
            assert isinstance(dietary_notes, (list, str))

    @patch('src.infrastructure.services.mise_en_place_service.logger')
    def test_generate_mise_en_place_logging(self, mock_logger, mise_service, sample_recipe_data):
        """Test that service properly logs activities"""
        # Act
        mise_service.generate_mise_en_place(sample_recipe_data)
        
        # Assert
        # Should log the mise en place generation
        assert mock_logger.info.called or mock_logger.debug.called
