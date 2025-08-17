import pytest


def test_parse_response_text_with_markdown_json():
    from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
    s = GeminiRecipeGeneratorService()
    text = """
    ```json
    [
      {"name": "Dish", "ingredients": [], "steps": []}
    ]
    ```
    """
    parsed = s._parse_response_text(text)
    assert isinstance(parsed, list)
    assert parsed[0]['name'] == 'Dish'


def test_parse_response_text_invalid_raises():
    from src.infrastructure.ai.gemini_recipe_generator_service import GeminiRecipeGeneratorService
    s = GeminiRecipeGeneratorService()
    with pytest.raises(ValueError):
        s._parse_response_text('no json here')

