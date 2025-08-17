import pytest
from unittest.mock import MagicMock, patch


@patch('src.infrastructure.ai.gemini_recipe_generator_service.ai_cache')
@patch('src.infrastructure.ai.gemini_recipe_generator_service.Config')
@patch('src.infrastructure.ai.gemini_recipe_generator_service.genai')
def test_gemini_generator_fast_parser_and_error_handling(mock_genai, mock_config, mock_cache):
    mock_config.GEMINI_API_KEY = 'k'
    # Force model to return markdown JSON requiring fast parser
    model = MagicMock()
    response = MagicMock()
    response.text = "```json\n[{\"title\":\"X\",\"ingredients\":[],\"steps\":[]}]\n```"
    model.generate_content.return_value = response
    mock_genai.GenerativeModel.return_value = model
    mock_cache.get_cached_response.return_value = None

    from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
    s = GeminiRecipeGeneratorService()
    s.performance_mode = True  # Trigger _fast_parse_response
    data = {"ingredients": [], "priorities": [], "preferences": [], "user_profile": {"language": "es"}}
    ok = s.generate_recipes(data, num_recipes=1)
    assert ok['total_recipes'] >= 1

    # Now simulate model error and ensure ValueError is raised
    model.generate_content.side_effect = Exception('API error')
    with pytest.raises(ValueError):
        s.generate_recipes(data, num_recipes=1)

