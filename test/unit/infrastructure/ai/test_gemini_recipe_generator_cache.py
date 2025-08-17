import pytest
from unittest.mock import MagicMock, patch


@patch('src.infrastructure.ai.gemini_recipe_generator_service.ai_cache')
@patch('src.infrastructure.ai.gemini_recipe_generator_service.Config')
@patch('src.infrastructure.ai.gemini_recipe_generator_service.genai')
def test_gemini_recipe_generator_uses_cache(mock_genai, mock_config, mock_cache):
    mock_config.GEMINI_API_KEY = 'test-key'

    # Return cached text
    cached_text = '[{"name": "Cached Dish", "ingredients": [], "steps": []}]'
    mock_cache.get_cached_response.return_value = cached_text

    from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
    service = GeminiRecipeGeneratorService()
    service.performance_mode = False  # ensure _parse_response_text path

    data = {"ingredients": [], "priorities": [], "preferences": [], "user_profile": {"language": "es"}}
    result = service.generate_recipes(data, num_recipes=1)

    # Should not call model.generate_content when cache hits
    assert not mock_genai.GenerativeModel.return_value.generate_content.called
    assert result['generated_recipes'][0]['name'] == 'Cached Dish'

