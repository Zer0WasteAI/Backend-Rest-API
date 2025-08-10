"""
Unit tests for GeminiAdapterService
Tests the Gemini AI integration service for food analysis and image generation
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image

from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.shared.exceptions.custom import UnidentifiedImageException, InvalidResponseFormatException


class TestGeminiAdapterService:
    """Test suite for GeminiAdapterService"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock google.generativeai module"""
        with patch('src.infrastructure.ai.gemini_adapter_service.genai') as mock:
            mock_model = Mock()
            mock.GenerativeModel.return_value = mock_model
            yield mock, mock_model
    
    @pytest.fixture
    def mock_config(self):
        """Mock Config class"""
        with patch('src.infrastructure.ai.gemini_adapter_service.Config') as mock:
            mock.GEMINI_API_KEY = "test_api_key"
            yield mock
    
    @pytest.fixture
    def gemini_service(self, mock_genai, mock_config):
        """GeminiAdapterService instance with mocked dependencies"""
        mock_genai_module, mock_model = mock_genai
        service = GeminiAdapterService()
        service.model = mock_model
        service.image_gen_model = mock_model
        return service
    
    @pytest.fixture
    def sample_image_files(self):
        """Sample image files for testing"""
        # Create mock file objects
        mock_files = []
        for i in range(3):
            mock_file = Mock()
            mock_file.filename = f"image_{i+1}.jpg"
            mock_file.read.return_value = b"fake_image_data"
            mock_files.append(mock_file)
        return mock_files
    
    def test_initialization(self, mock_genai, mock_config):
        """Test GeminiAdapterService initialization"""
        # Arrange
        mock_genai_module, mock_model = mock_genai
        
        # Act
        service = GeminiAdapterService()
        
        # Assert
        mock_genai_module.configure.assert_called_once_with(api_key="test_api_key")
        assert mock_genai_module.GenerativeModel.call_count == 2  # Two models created
        assert service.performance_mode is True
        assert service.max_workers == 8
        assert isinstance(service.generation_config_base, dict)
    
    def test_parse_response_text_valid_json(self, gemini_service):
        """Test parsing valid JSON response"""
        # Arrange
        json_data = {"ingredients": [{"name": "tomato", "confidence": 0.95}]}
        response_text = json.dumps(json_data)
        
        # Act
        result = gemini_service._parse_response_text(response_text)
        
        # Assert
        assert result == json_data
    
    def test_parse_response_text_with_code_blocks(self, gemini_service):
        """Test parsing JSON wrapped in code blocks"""
        # Arrange
        json_data = {"foods": [{"name": "pizza", "confidence": 0.90}]}
        response_text = f"```json\n{json.dumps(json_data)}\n```"
        
        # Act
        result = gemini_service._parse_response_text(response_text)
        
        # Assert
        assert result == json_data
    
    def test_parse_response_text_with_backticks_only(self, gemini_service):
        """Test parsing JSON wrapped in backticks without json label"""
        # Arrange
        json_data = {"test": "data"}
        response_text = f"```\n{json.dumps(json_data)}\n```"
        
        # Act
        result = gemini_service._parse_response_text(response_text)
        
        # Assert
        assert result == json_data
    
    def test_parse_response_text_invalid_json(self, gemini_service):
        """Test parsing invalid JSON raises exception"""
        # Arrange
        invalid_json = "{ invalid json content"
        
        # Act & Assert
        with pytest.raises(InvalidResponseFormatException):
            gemini_service._parse_response_text(invalid_json)
    
    @patch('src.infrastructure.ai.gemini_adapter_service.ai_cache')
    def test_generate_ingredient_image_success(self, mock_cache, gemini_service):
        """Test successful ingredient image generation"""
        # Arrange
        ingredient_name = "tomato"
        description = "Fresh red tomato"
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock successful image generation
        mock_response = Mock()
        mock_response.parts = [Mock()]
        mock_response.parts[0].inline_data.data = base64.b64encode(b"fake_image_data").decode()
        mock_response.parts[0].inline_data.mime_type = "image/png"
        
        gemini_service.image_gen_model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.generate_ingredient_image(ingredient_name, description)
        
        # Assert
        assert result is not None
        assert isinstance(result, BytesIO)
        
        # Verify cache was checked and set
        cache_key = f"ingredient_image_{ingredient_name}_{hash(description)}"
        mock_cache.get.assert_called_once_with(cache_key)
        mock_cache.set.assert_called_once()
    
    @patch('src.infrastructure.ai.gemini_adapter_service.ai_cache')
    def test_generate_ingredient_image_cache_hit(self, mock_cache, gemini_service):
        """Test ingredient image generation with cache hit"""
        # Arrange
        ingredient_name = "carrot"
        cached_image_data = b"cached_image_data"
        mock_cache.get.return_value = cached_image_data
        
        # Act
        result = gemini_service.generate_ingredient_image(ingredient_name)
        
        # Assert
        assert result is not None
        assert isinstance(result, BytesIO)
        assert result.getvalue() == cached_image_data
        
        # Verify model was not called
        gemini_service.image_gen_model.generate_content.assert_not_called()
    
    def test_generate_ingredient_image_failure(self, gemini_service):
        """Test ingredient image generation failure"""
        # Arrange
        ingredient_name = "unknown"
        
        # Mock generation failure
        gemini_service.image_gen_model.generate_content.side_effect = Exception("Generation failed")
        
        with patch('src.infrastructure.ai.gemini_adapter_service.ai_cache') as mock_cache:
            mock_cache.get.return_value = None
            
            # Act
            result = gemini_service.generate_ingredient_image(ingredient_name)
            
            # Assert
            assert result is None
    
    @patch('src.infrastructure.ai.gemini_adapter_service.ai_cache')
    def test_generate_food_image_success(self, mock_cache, gemini_service):
        """Test successful food image generation"""
        # Arrange
        food_name = "pizza"
        description = "Delicious homemade pizza"
        main_ingredients = ["dough", "tomato", "cheese"]
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock successful image generation
        mock_response = Mock()
        mock_response.parts = [Mock()]
        mock_response.parts[0].inline_data.data = base64.b64encode(b"fake_food_image").decode()
        mock_response.parts[0].inline_data.mime_type = "image/png"
        
        gemini_service.image_gen_model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.generate_food_image(food_name, description, main_ingredients)
        
        # Assert
        assert result is not None
        assert isinstance(result, BytesIO)
        
        # Verify cache operations
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
    
    def test_analyze_environmental_impact(self, gemini_service):
        """Test environmental impact analysis"""
        # Arrange
        ingredient_name = "beef"
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "carbon_footprint": {"value": 60.0, "unit": "kg CO2"},
            "water_footprint": {"value": 15400, "unit": "liters"},
            "environmental_message": "High environmental impact"
        })
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.analyze_environmental_impact(ingredient_name)
        
        # Assert
        assert isinstance(result, dict)
        assert "carbon_footprint" in result
        assert "water_footprint" in result
        assert result["carbon_footprint"]["value"] == 60.0
        assert result["water_footprint"]["unit"] == "liters"
    
    def test_analyze_environmental_impact_invalid_response(self, gemini_service):
        """Test environmental impact analysis with invalid response"""
        # Arrange
        ingredient_name = "unknown"
        
        # Mock invalid response
        mock_response = Mock()
        mock_response.text = "invalid json response"
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(InvalidResponseFormatException):
            gemini_service.analyze_environmental_impact(ingredient_name)
    
    def test_generate_utilization_ideas(self, gemini_service):
        """Test utilization ideas generation"""
        # Arrange
        ingredient_name = "carrot"
        description = "Fresh orange carrot"
        
        # Mock successful response
        expected_ideas = {
            "conservation_tips": ["Store in refrigerator", "Use within 7 days"],
            "recipe_ideas": ["Carrot soup", "Roasted carrots"],
            "preparation_methods": ["Raw", "Steamed", "Roasted"]
        }
        
        mock_response = Mock()
        mock_response.text = json.dumps(expected_ideas)
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.generate_utilization_ideas(ingredient_name, description)
        
        # Assert
        assert result == expected_ideas
        assert "conservation_tips" in result
        assert "recipe_ideas" in result
        assert isinstance(result["conservation_tips"], list)
    
    @patch('src.infrastructure.ai.gemini_adapter_service.ThreadPoolExecutor')
    def test_recognize_ingredients_parallel_processing(self, mock_executor, gemini_service, sample_image_files):
        """Test ingredient recognition with parallel processing"""
        # Arrange
        mock_future = Mock()
        mock_future.result.return_value = {"ingredients": [{"name": "tomato", "confidence": 0.95}]}
        
        mock_executor_instance = Mock()
        mock_executor_instance.submit.return_value = mock_future
        mock_executor_instance.__enter__.return_value = mock_executor_instance
        mock_executor_instance.__exit__.return_value = None
        mock_executor.return_value = mock_executor_instance
        
        # Act
        result = gemini_service.recognize_ingredients(sample_image_files)
        
        # Assert
        assert isinstance(result, dict)
        mock_executor.assert_called_once_with(max_workers=8)
    
    def test_suggest_storage_type(self, gemini_service):
        """Test storage type suggestion"""
        # Arrange
        food_name = "milk"
        
        # Mock response
        mock_response = Mock()
        mock_response.text = json.dumps({"storage_type": "Refrigerated"})
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.suggest_storage_type(food_name)
        
        # Assert
        assert result == "Refrigerated"
    
    def test_category_autotag(self, gemini_service):
        """Test category auto-tagging"""
        # Arrange
        food_name = "apple"
        expected_tags = ["Fruit", "Sweet", "Healthy"]
        
        # Mock response
        mock_response = Mock()
        mock_response.text = json.dumps({"categories": expected_tags})
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.category_autotag(food_name)
        
        # Assert
        assert result == expected_tags
        assert isinstance(result, list)
    
    def test_match_allergens(self, gemini_service):
        """Test allergen matching"""
        # Arrange
        food_name = "bread"
        user_allergens = ["gluten", "nuts", "dairy"]
        expected_matches = ["gluten"]
        
        # Mock response
        mock_response = Mock()
        mock_response.text = json.dumps({"matched_allergens": expected_matches})
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.match_allergens(food_name, user_allergens)
        
        # Assert
        assert result == expected_matches
        assert "gluten" in result
    
    @pytest.mark.parametrize("food_name,expected_storage", [
        ("milk", "Refrigerated"),
        ("bread", "Room Temperature"),
        ("ice_cream", "Frozen"),
    ])
    def test_suggest_storage_type_various_foods(self, gemini_service, food_name, expected_storage):
        """Parametrized test for storage suggestions"""
        # Arrange
        mock_response = Mock()
        mock_response.text = json.dumps({"storage_type": expected_storage})
        
        gemini_service.model.generate_content.return_value = mock_response
        
        # Act
        result = gemini_service.suggest_storage_type(food_name)
        
        # Assert
        assert result == expected_storage
    
    def test_performance_mode_configuration(self, gemini_service):
        """Test that performance mode configurations are properly set"""
        # Assert
        assert gemini_service.performance_mode is True
        assert gemini_service.max_workers == 8
        assert gemini_service.generation_config_base["temperature"] == 0.4
        assert gemini_service.generation_config_base["max_output_tokens"] == 1024
        assert gemini_service.generation_config_base["candidate_count"] == 1
    
    def test_model_initialization_with_correct_names(self, mock_genai, mock_config):
        """Test that models are initialized with correct names"""
        # Arrange
        mock_genai_module, _ = mock_genai
        
        # Act
        service = GeminiAdapterService()
        
        # Assert
        calls = mock_genai_module.GenerativeModel.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == "gemini-2.5-flash-lite-preview-06-17"
        assert calls[1][0][0] == "gemini-2.0-flash-preview-image-generation"
    
    def test_error_handling_in_image_generation(self, gemini_service):
        """Test error handling in image generation methods"""
        # Arrange
        gemini_service.image_gen_model.generate_content.side_effect = Exception("API Error")
        
        with patch('src.infrastructure.ai.gemini_adapter_service.ai_cache') as mock_cache:
            mock_cache.get.return_value = None
            
            # Act
            ingredient_result = gemini_service.generate_ingredient_image("test")
            food_result = gemini_service.generate_food_image("test")
            
            # Assert
            assert ingredient_result is None
            assert food_result is None
    
    @patch('base64.b64decode')
    def test_image_decoding_in_generation(self, mock_b64decode, gemini_service):
        """Test base64 image decoding in image generation"""
        # Arrange
        fake_image_data = b"fake_decoded_image"
        mock_b64decode.return_value = fake_image_data
        
        mock_response = Mock()
        mock_response.parts = [Mock()]
        mock_response.parts[0].inline_data.data = "fake_encoded_data"
        mock_response.parts[0].inline_data.mime_type = "image/png"
        
        gemini_service.image_gen_model.generate_content.return_value = mock_response
        
        with patch('src.infrastructure.ai.gemini_adapter_service.ai_cache') as mock_cache:
            mock_cache.get.return_value = None
            
            # Act
            result = gemini_service.generate_ingredient_image("test")
            
            # Assert
            assert result is not None
            mock_b64decode.assert_called_once_with("fake_encoded_data")
            assert result.getvalue() == fake_image_data