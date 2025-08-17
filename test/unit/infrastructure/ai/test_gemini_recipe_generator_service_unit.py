import pytest
from unittest.mock import MagicMock, patch


@patch('src.infrastructure.ai.gemini_recipe_generator_service.ai_cache')
@patch('src.infrastructure.ai.gemini_recipe_generator_service.Config')
@patch('src.infrastructure.ai.gemini_recipe_generator_service.genai')
def test_gemini_recipe_generator_service_parses_response(mock_genai, mock_config, mock_cache):
    mock_config.GEMINI_API_KEY = 'test-key'

    # Mock GenerativeModel and response
    model = MagicMock()
    response = MagicMock()
    response.text = '[{"name": "Simple Salad", "ingredients": [], "steps": []}]'
    model.generate_content.return_value = response
    mock_genai.GenerativeModel.return_value = model

    # Disable cache to force generation
    mock_cache.get_cached_response.return_value = None

    from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
    service = GeminiRecipeGeneratorService()
    # Force classic parser to avoid relying on _fast_parse_response
    service.performance_mode = False
    data = {"ingredients": [], "priorities": [], "preferences": [], "user_profile": {"language": "es"}}
    result = service.generate_recipes(data, num_recipes=1)

    assert isinstance(result, dict)
    assert 'generated_recipes' in result
    assert len(result['generated_recipes']) == 1
    model.generate_content.assert_called_once()
