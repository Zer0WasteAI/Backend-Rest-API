import os

base_path = ""

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'zero_waste_api',
            "route": '/api/docs/v1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "ZeroWasteAI API",
        "description": "API para la gestión de endpoints de ZeroWasteAI",
        "version": "0.0.1",
        "termsOfService": "https://zer0wasteai.com/terms/",
        "contact": {
            "email": "zerowasteai4@gmail.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization. Escribe: **Bearer &lt;tu_token&gt;**"
        }
    },
    "security": [
        {"Bearer": []}
    ],
    "host": "localhost:3000",
    "basePath": base_path,
    "schemes": [
        "http",
        "https"
    ]
}