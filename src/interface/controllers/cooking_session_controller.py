from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime
from typing import Optional

from src.application.use_cases.cooking_session.start_cooking_session_use_case import StartCookingSessionUseCase
from src.application.use_cases.cooking_session.complete_step_use_case import CompleteStepUseCase
from src.application.use_cases.cooking_session.finish_cooking_session_use_case import FinishCookingSessionUseCase
from src.application.use_cases.recipes.get_mise_en_place_use_case import GetMiseEnPlaceUseCase
from src.application.factories.cooking_session_factory import (
    make_start_cooking_session_use_case,
    make_complete_step_use_case,
    make_finish_cooking_session_use_case,
    make_get_mise_en_place_use_case
)
from src.infrastructure.services.idempotency_service import IdempotencyService
from src.infrastructure.optimization.rate_limiter import smart_rate_limit
from src.shared.exceptions.custom import InvalidRequestDataException, RecipeNotFoundException
from src.infrastructure.db.base import db
import json

cooking_session_bp = Blueprint("cooking_session", __name__)

def check_idempotency(endpoint_name: str):
    """Decorator to handle idempotency for POST requests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if request.method == 'POST':
                idempotency_key = request.headers.get('Idempotency-Key')
                if not idempotency_key:
                    return jsonify({"error": "Idempotency-Key header is required for POST requests"}), 400
                
                user_uid = get_jwt_identity()
                request_body = request.get_json() or {}
                
                idempotency_service = IdempotencyService(db)
                
                # Check if request was already processed
                cached_response = idempotency_service.check_idempotency(
                    idempotency_key=idempotency_key,
                    user_uid=user_uid,
                    endpoint=endpoint_name,
                    request_body=request_body
                )
                
                if cached_response:
                    status_code, response_body = cached_response
                    return response_body, int(status_code)
                
                # Process new request
                response = func(*args, **kwargs)
                
                # Store response for future idempotency checks
                if isinstance(response, tuple):
                    response_data, status_code = response
                else:
                    response_data, status_code = response, 200
                
                idempotency_service.store_response(
                    idempotency_key=idempotency_key,
                    user_uid=user_uid,
                    endpoint=endpoint_name,
                    request_body=request_body,
                    status_code=str(status_code),
                    response_body=json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
                )
                
                return response_data, status_code
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


@cooking_session_bp.route("/recipes/<recipe_uid>/mise_en_place", methods=["GET"])
@jwt_required()
@smart_rate_limit('data_read')
@swag_from({
    'tags': ['Cooking Session'],
    'summary': 'Obtener mise en place para una receta',
    'description': '''
Obtiene la mise en place (preparación previa) para una receta específica con el número de porciones indicado.

### Funcionalidad:
- **Tools**: Lista de herramientas necesarias
- **Preheat**: Instrucciones de precalentamiento
- **Prep Tasks**: Tareas de preparación con cantidades escaladas
- **Measured Ingredients**: Ingredientes medidos con sugerencias FEFO de lotes

### Sugerencias FEFO:
- Utiliza el algoritmo First Expired, First Out
- Sugiere lotes específicos del inventario del usuario
- NO descuenta stock (solo sugiere)

### Escalado por Porciones:
- Todas las cantidades se escalan según el parámetro servings
- Base: recetas asumen 2 porciones por defecto
    ''',
    'parameters': [
        {
            'name': 'recipe_uid',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'UID de la receta'
        },
        {
            'name': 'servings',
            'in': 'query',
            'type': 'integer',
            'minimum': 1,
            'default': 2,
            'description': 'Número de porciones'
        }
    ],
    'responses': {
        200: {
            'description': 'Mise en place generada exitosamente',
            'examples': {
                'application/json': {
                    "recipe_uid": "rcp_aji_gallina_01",
                    "servings": 3,
                    "tools": ["olla mediana", "sartén", "cuchillo", "tabla"],
                    "preheat": [
                        {"device": "stove", "setting": "medium", "duration_ms": 60000}
                    ],
                    "prep_tasks": [
                        {
                            "id": "mp1",
                            "text": "Picar cebolla en cubos (120 g)",
                            "ingredient_uid": "ing_onion",
                            "suggested_qty": 120,
                            "unit": "g"
                        }
                    ],
                    "measured_ingredients": [
                        {
                            "ingredient_uid": "ing_onion",
                            "qty": 120,
                            "unit": "g",
                            "lot_suggestion": "batch_777"
                        }
                    ]
                }
            }
        },
        404: {
            'description': 'Receta no encontrada'
        }
    }
})
def get_mise_en_place(recipe_uid: str):
    """Get mise en place for a recipe"""
    user_uid = get_jwt_identity()
    servings = request.args.get('servings', default=2, type=int)
    
    if servings <= 0:
        raise InvalidRequestDataException(details={"servings": "Must be positive"})
    
    try:
        use_case = make_get_mise_en_place_use_case()
        mise_en_place = use_case.execute(
            recipe_uid=recipe_uid,
            servings=servings,
            user_uid=user_uid
        )
        
        return jsonify(mise_en_place.to_dict()), 200
        
    except RecipeNotFoundException as e:
        return jsonify({"error": str(e)}), 404


@cooking_session_bp.route("/cooking_session/start", methods=["POST"])
@jwt_required()
@smart_rate_limit('data_write')
@check_idempotency('cooking_session_start')
@swag_from({
    'tags': ['Cooking Session'],
    'summary': 'Iniciar sesión de cocina',
    'description': '''
Inicia una nueva sesión de cocina para una receta específica.

### Funcionalidad:
- Valida que la receta existe
- Verifica límite de sesiones activas (máximo 3)
- Crea sesión con pasos inicializados
- Requiere header Idempotency-Key

### Niveles de Cocina:
- **beginner**: Instrucciones detalladas y tiempos extendidos
- **intermediate**: Instrucciones estándar
- **advanced**: Instrucciones concisas
    ''',
    'parameters': [
        {
            'name': 'Idempotency-Key',
            'in': 'header',
            'required': True,
            'type': 'string',
            'description': 'Clave de idempotencia UUID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['recipe_uid', 'servings', 'level', 'started_at'],
                'properties': {
                    'recipe_uid': {'type': 'string'},
                    'servings': {'type': 'integer', 'minimum': 1},
                    'level': {'type': 'string', 'enum': ['beginner', 'intermediate', 'advanced']},
                    'started_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Sesión iniciada exitosamente',
            'examples': {
                'application/json': {
                    "session_id": "cook_9a1f",
                    "status": "running"
                }
            }
        },
        400: {'description': 'Datos inválidos o demasiadas sesiones activas'},
        404: {'description': 'Receta no encontrada'}
    }
})
def start_cooking_session():
    """Start a new cooking session"""
    user_uid = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        raise InvalidRequestDataException(details={"body": "Request body is required"})
    
    required_fields = ['recipe_uid', 'servings', 'level', 'started_at']
    for field in required_fields:
        if field not in data:
            raise InvalidRequestDataException(details={field: "This field is required"})
    
    try:
        started_at = datetime.fromisoformat(data['started_at'].replace('Z', '+00:00'))
    except ValueError:
        raise InvalidRequestDataException(details={"started_at": "Invalid datetime format"})
    
    try:
        use_case = make_start_cooking_session_use_case()
        session = use_case.execute(
            recipe_uid=data['recipe_uid'],
            servings=data['servings'],
            level=data['level'],
            user_uid=user_uid,
            started_at=started_at
        )
        
        return jsonify({
            "session_id": session.session_id,
            "status": "running"
        }), 201
        
    except RecipeNotFoundException as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@cooking_session_bp.route("/cooking_session/complete_step", methods=["POST"])
@jwt_required()
@smart_rate_limit('data_write')
@check_idempotency('cooking_session_complete_step')
@swag_from({
    'tags': ['Cooking Session'],
    'summary': 'Completar paso de cocina',
    'description': '''
Completa un paso de la sesión de cocina con consumos de ingredientes.

### Funcionalidad Transaccional:
- Lock por lote para prevenir condiciones de carrera
- Validación de cantidad disponible
- Descuento atómico de stock FEFO
- Registro de consumo en log

### Validaciones:
- Verifica pertenencia de lotes al usuario
- Valida fechas de vencimiento (use_by)
- Confirma cantidad suficiente en lotes
- Estado de lote válido para consumo
    ''',
    'parameters': [
        {
            'name': 'Idempotency-Key',
            'in': 'header',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['session_id', 'step_id'],
                'properties': {
                    'session_id': {'type': 'string'},
                    'step_id': {'type': 'string'},
                    'timer_ms': {'type': 'integer'},
                    'consumptions': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['ingredient_uid', 'lot_id', 'qty', 'unit'],
                            'properties': {
                                'ingredient_uid': {'type': 'string'},
                                'lot_id': {'type': 'string'},
                                'qty': {'type': 'number'},
                                'unit': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Paso completado exitosamente',
            'examples': {
                'application/json': {
                    "ok": True,
                    "inventory_updates": [
                        {"lot_id": "batch_777", "new_qty": 120},
                        {"lot_id": "batch_552", "new_qty": 490}
                    ]
                }
            }
        }
    }
})
def complete_cooking_step():
    """Complete a cooking step with ingredient consumptions"""
    user_uid = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        raise InvalidRequestDataException(details={"body": "Request body is required"})
    
    required_fields = ['session_id', 'step_id']
    for field in required_fields:
        if field not in data:
            raise InvalidRequestDataException(details={field: "This field is required"})
    
    try:
        use_case = make_complete_step_use_case()
        result = use_case.execute(
            session_id=data['session_id'],
            step_id=data['step_id'],
            user_uid=user_uid,
            timer_ms=data.get('timer_ms'),
            consumptions=data.get('consumptions', [])
        )
        
        return jsonify(result), 200
        
    except (RecipeNotFoundException, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@cooking_session_bp.route("/cooking_session/finish", methods=["POST"])
@jwt_required()
@smart_rate_limit('data_write')
@check_idempotency('cooking_session_finish')
@swag_from({
    'tags': ['Cooking Session'],
    'summary': 'Finalizar sesión de cocina',
    'description': '''
Finaliza una sesión de cocina y calcula métricas ambientales.

### Funcionalidades:
- Marca sesión como finalizada
- Calcula impacto ambiental real basado en consumos
- Genera sugerencia de sobras si aplica
- Guarda notas y foto opcional

### Cálculo Ambiental:
- Basado en consumos reales de la sesión
- CO2 evitado vs. alternativas comerciales
- Agua conservada en producción
- Desperdicio de alimentos reducido
    ''',
    'parameters': [
        {
            'name': 'Idempotency-Key',
            'in': 'header',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['session_id'],
                'properties': {
                    'session_id': {'type': 'string'},
                    'notes': {'type': 'string'},
                    'photo_url': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Sesión finalizada exitosamente',
            'examples': {
                'application/json': {
                    "ok": True,
                    "environmental_saving": {
                        "co2e_kg": 0.38,
                        "water_l": 95,
                        "waste_kg": 0.12
                    },
                    "leftover_suggestion": {
                        "portions": 2,
                        "eat_by": "2025-08-18"
                    }
                }
            }
        }
    }
})
def finish_cooking_session():
    """Finish a cooking session"""
    user_uid = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'session_id' not in data:
        raise InvalidRequestDataException(details={"session_id": "This field is required"})
    
    try:
        use_case = make_finish_cooking_session_use_case()
        result = use_case.execute(
            session_id=data['session_id'],
            user_uid=user_uid,
            notes=data.get('notes'),
            photo_url=data.get('photo_url')
        )
        
        return jsonify(result), 200
        
    except (RecipeNotFoundException, ValueError) as e:
        return jsonify({"error": str(e)}), 400