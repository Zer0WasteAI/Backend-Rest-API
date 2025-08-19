from src.config.swagger_config import swagger_config, swagger_template


def test_swagger_config_and_template_shapes():
    assert isinstance(swagger_config, dict)
    assert "specs" in swagger_config
    assert any(isinstance(s, dict) for s in swagger_config.get("specs", []))

    assert isinstance(swagger_template, dict)
    assert swagger_template.get("swagger") in ("2.0", "3.0", "3.0.0")
    info = swagger_template.get("info", {})
    assert "title" in info and "version" in info

