from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from

from src.infrastructure.db.base import db
from src.interface.serializers.image_reference_serializer import ImageReferencePublicSchema
from src.interface.serializers.item_name_serializer import ItemNameSchema
from src.interface.serializers.upload_image_serializer import UploadImageRequestSchema, UploadImageResponseSchema
from src.application.factories.image_management_usecase_factory import (
    make_search_similar_images_use_case,
    make_assign_image_reference_use_case,
    make_sync_image_loader_use_case,
    make_upload_image_use_case
)
from src.infrastructure.optimization.rate_limiter import smart_rate_limit
from src.shared.exceptions.custom import InvalidRequestDataException
from src.shared.decorators.internal_only import internal_only
from src.domain.value_objects.upload_request import UploadRequest

image_management_bp = Blueprint('image_management', __name__)
public_schema = ImageReferencePublicSchema()
item_name_schema = ItemNameSchema()
upload_request_schema = UploadImageRequestSchema()
upload_response_schema = UploadImageResponseSchema()

@image_management_bp.route("/assign_image", methods=["POST"])
@jwt_required()
@smart_rate_limit('data_write')  # 🛡️ Rate limit: 40 requests/min for image processing
@swag_from({
    'tags': ['Image Management'],
    'summary': 'Asignar imagen de referencia a un ingrediente',
    'description': '''
Asigna automáticamente una imagen de referencia a un ingrediente específico desde la base de datos de imágenes.

### Funcionamiento:
- **Búsqueda automática**: Busca la mejor imagen disponible para el ingrediente
- **Algoritmo de matching**: Usa similitud semántica para encontrar la imagen más apropiada
- **Asignación persistente**: Guarda la referencia en la base de datos
- **Optimización**: Prioriza imágenes de alta calidad y relevancia
- **Fallback inteligente**: Si no encuentra imagen exacta, busca similares

### Proceso de Asignación:
1. **Análisis del nombre**: Procesa el nombre del ingrediente
2. **Búsqueda en base de datos**: Consulta imágenes disponibles
3. **Scoring de relevancia**: Calcula puntuación de similitud
4. **Selección óptima**: Escoge la imagen con mejor puntuación
5. **Asignación y guardado**: Crea la referencia en la base de datos

### Casos de Uso:
- Asignar imágenes a ingredientes recién agregados
- Actualizar referencias de imágenes obsoletas
- Completar catálogo visual de ingredientes
- Mejorar experiencia visual de la aplicación
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['item_name'],
                'properties': {
                    'item_name': {
                        'type': 'string',
                        'description': 'Nombre del ingrediente para asignar imagen',
                        'example': 'tomate cherry'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Imagen asignada exitosamente',
            'examples': {
                'application/json': {
                    "uid": "img_ref_123456789",
                    "name": "tomate cherry",
                    "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Ftomate_cherry_001.jpg",
                    "image_type": "ingredient",
                    "confidence_score": 0.95,
                    "assigned_at": "2024-01-16T19:15:00Z",
                    "source": "database_match",
                    "alternative_images": [
                        {
                            "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Ftomate_cherry_002.jpg",
                            "confidence_score": 0.88
                        },
                        {
                            "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Ftomate_cherry_003.jpg",
                            "confidence_score": 0.82
                        }
                    ],
                    "assignment_metadata": {
                        "search_query": "tomate cherry",
                        "total_candidates": 15,
                        "processing_time_ms": 245,
                        "algorithm_version": "semantic_v2.1"
                    }
                }
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid request data',
                    'details': {
                        'item_name': 'Este campo es requerido'
                    }
                }
            }
        },
        404: {
            'description': 'No se encontró imagen apropiada',
            'examples': {
                'application/json': {
                    'error': 'No suitable image found',
                    'details': 'No se encontró una imagen apropiada para el ingrediente especificado',
                    'item_name': 'ingrediente_raro',
                    'suggestions': [
                        'Verifica la ortografía del nombre del ingrediente',
                        'Prueba con un nombre más general',
                        'Considera subir una imagen personalizada'
                    ]
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
def assign_image():
    json_data = request.get_json()
    errors = item_name_schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    item_name = json_data.get("item_name")
    use_case = make_assign_image_reference_use_case(db)
    result = use_case.execute(item_name=item_name)

    serialized = public_schema.dump(result)
    return jsonify(serialized), 200

@image_management_bp.route("/search_similar_images", methods=["POST"])
@jwt_required()
@smart_rate_limit('data_read')  # 🛡️ Rate limit: 100 requests/min for image search
@swag_from({
    'tags': ['Image Management'],
    'summary': 'Buscar imágenes similares a un ingrediente',
    'description': '''
Busca múltiples imágenes similares a un ingrediente específico en la base de datos de imágenes.

### Características de Búsqueda:
- **Múltiples resultados**: Retorna varias opciones de imágenes similares
- **Ordenamiento por relevancia**: Resultados ordenados por puntuación de similitud
- **Análisis semántico**: Usa procesamiento de lenguaje natural para matching
- **Variedad visual**: Incluye diferentes ángulos y presentaciones del ingrediente
- **Filtrado de calidad**: Solo incluye imágenes de alta resolución y calidad

### Algoritmo de Similitud:
- **Análisis textual**: Procesamiento del nombre del ingrediente
- **Matching semántico**: Búsqueda por significado, no solo texto exacto
- **Sinónimos**: Incluye variaciones y nombres alternativos
- **Contexto culinario**: Considera contexto gastronómico y regional
- **Scoring avanzado**: Puntuación basada en múltiples factores

### Casos de Uso:
- Explorar opciones visuales para un ingrediente
- Seleccionar la mejor imagen de referencia
- Verificar disponibilidad de imágenes antes de asignación
- Análisis de cobertura visual del catálogo
- Investigación y desarrollo de nuevas referencias
    ''',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['item_name'],
                'properties': {
                    'item_name': {
                        'type': 'string',
                        'description': 'Nombre del ingrediente para buscar imágenes similares',
                        'example': 'manzana'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Imágenes similares encontradas exitosamente',
            'examples': {
                'application/json': [
                    {
                        "uid": "img_ref_001",
                        "name": "manzana roja",
                        "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Fmanzana_roja_001.jpg",
                        "image_type": "ingredient",
                        "confidence_score": 0.98,
                        "similarity_reason": "Coincidencia exacta de ingrediente",
                        "quality_score": 0.95,
                        "resolution": "1920x1080",
                        "file_size_kb": 245
                    },
                    {
                        "uid": "img_ref_002",
                        "name": "manzana verde",
                        "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Fmanzana_verde_001.jpg",
                        "image_type": "ingredient",
                        "confidence_score": 0.92,
                        "similarity_reason": "Misma familia de ingrediente",
                        "quality_score": 0.88,
                        "resolution": "1600x900",
                        "file_size_kb": 198
                    },
                    {
                        "uid": "img_ref_003",
                        "name": "manzana amarilla",
                        "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Fmanzana_amarilla_001.jpg",
                        "image_type": "ingredient",
                        "confidence_score": 0.89,
                        "similarity_reason": "Variedad del mismo ingrediente",
                        "quality_score": 0.91,
                        "resolution": "1440x810",
                        "file_size_kb": 220
                    },
                    {
                        "uid": "img_ref_004",
                        "name": "fruta roja",
                        "image_path": "https://firebasestorage.googleapis.com/v0/b/project/o/images%2Ffruta_roja_mix_001.jpg",
                        "image_type": "ingredient",
                        "confidence_score": 0.75,
                        "similarity_reason": "Categoría similar - frutas rojas",
                        "quality_score": 0.82,
                        "resolution": "1280x720",
                        "file_size_kb": 185
                    }
                ]
            }
        },
        400: {
            'description': 'Datos de entrada inválidos',
            'examples': {
                'application/json': {
                    'error': 'Invalid request data',
                    'details': {
                        'item_name': 'Este campo es requerido'
                    }
                }
            }
        },
        404: {
            'description': 'No se encontraron imágenes similares',
            'examples': {
                'application/json': {
                    'message': 'No similar images found',
                    'search_term': 'ingrediente_inexistente',
                    'suggestions': [
                        'Verifica la ortografía del ingrediente',
                        'Prueba con términos más generales',
                        'Considera subir imágenes para este ingrediente'
                    ],
                    'similar_searches': [
                        'ingrediente_similar_1',
                        'ingrediente_similar_2'
                    ]
                }
            }
        },
        401: {
            'description': 'Token de autenticación inválido'
        },
        500: {
            'description': 'Error interno del servidor'
        }
    }
})
def search_similar_images():
    json_data = request.get_json()
    errors = item_name_schema.validate(json_data)
    if errors:
        raise InvalidRequestDataException(details=errors)

    item_name = json_data.get("item_name")
    use_case = make_search_similar_images_use_case(db)
    results = use_case.execute(item_name=item_name)

    serialized_list = public_schema.dump(results, many=True)
    return jsonify(serialized_list), 200

@image_management_bp.route("/sync_images", methods=["POST"])
@internal_only
@swag_from({
    'tags': ['Image Management'],
    'summary': 'Sincronizar imágenes con base de datos (Endpoint Interno)',
    'description': '''
Sincroniza las imágenes del almacenamiento con la base de datos. **Endpoint solo para uso interno del sistema.**

### Funcionalidad:
- **Sincronización automática**: Detecta nuevas imágenes en el almacenamiento
- **Actualización de base de datos**: Registra imágenes no catalogadas
- **Limpieza de referencias**: Elimina referencias a imágenes inexistentes
- **Indexación**: Actualiza índices de búsqueda y metadatos
- **Validación**: Verifica integridad de archivos e imágenes

### Proceso de Sincronización:
1. **Escaneo de almacenamiento**: Revisa todos los archivos de imagen
2. **Comparación con BD**: Identifica diferencias entre almacenamiento y base de datos
3. **Registro de nuevas**: Agrega metadatos de imágenes nuevas
4. **Limpieza de huérfanas**: Elimina referencias sin archivo correspondiente
5. **Actualización de índices**: Refresca índices de búsqueda

### Restricciones:
- **Solo uso interno**: Requiere decorador @internal_only
- **Operación costosa**: Puede tomar tiempo considerable
- **Uso programado**: Generalmente ejecutado por tareas cron
- **Monitoreo requerido**: Debe supervisarse para detectar errores

### Casos de Uso:
- Mantenimiento programado del sistema
- Recuperación después de fallos de sincronización
- Migración de imágenes
- Limpieza de base de datos
- Actualización masiva de metadatos
    ''',
    'responses': {
        200: {
            'description': 'Sincronización completada exitosamente',
            'examples': {
                'application/json': {
                    "message": "15 imágenes sincronizadas",
                    "sync_summary": {
                        "images_added": 12,
                        "images_updated": 3,
                        "orphaned_references_removed": 2,
                        "total_images_in_storage": 1847,
                        "total_references_in_db": 1845,
                        "sync_duration_seconds": 45.2,
                        "sync_completed_at": "2024-01-16T20:30:00Z"
                    },
                    "details": {
                        "new_images": [
                            {
                                "name": "aguacate_hass_001",
                                "path": "images/ingredients/aguacate_hass_001.jpg",
                                "size_kb": 234,
                                "resolution": "1920x1080"
                            },
                            {
                                "name": "quinoa_tricolor_001",
                                "path": "images/ingredients/quinoa_tricolor_001.jpg",
                                "size_kb": 198,
                                "resolution": "1600x900"
                            }
                        ],
                        "updated_images": [
                            {
                                "name": "tomate_cherry_001",
                                "changes": ["metadata_updated", "quality_score_recalculated"]
                            }
                        ],
                        "removed_references": [
                            {
                                "name": "imagen_eliminada_001",
                                "reason": "File not found in storage"
                            }
                        ]
                    }
                }
            }
        },
        403: {
            'description': 'Acceso denegado - Solo uso interno',
            'examples': {
                'application/json': {
                    'error': 'Access denied',
                    'details': 'Este endpoint es solo para uso interno del sistema',
                    'required_access': 'internal_only'
                }
            }
        },
        500: {
            'description': 'Error durante la sincronización',
            'examples': {
                'application/json': {
                    'error': 'Sync operation failed',
                    'details': 'Error accessing storage or database during sync',
                    'error_type': 'StorageConnectionException',
                    'partial_results': {
                        'images_processed': 145,
                        'images_remaining': 1702,
                        'last_successful_image': 'imagen_144.jpg'
                    }
                }
            }
        }
    }
})
def sync_images():
    use_case = make_sync_image_loader_use_case(db)
    added = use_case.execute()
    return jsonify({"message": f"{added} imágenes sincronizadas"}), 200


@image_management_bp.route("/upload_image", methods=["POST"])
@jwt_required()
@smart_rate_limit('data_write')  # 🛡️ Rate limit: 40 requests/min for image uploads
@swag_from({
    'tags': ['Image Management'],
    'summary': 'Upload image file to Firebase Storage',
    'description': 'Upload an image file and register it in the database for training or reference purposes',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'image',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Image file to upload (JPG, PNG, GIF, WEBP, max 10MB)'
        },
        {
            'name': 'item_name',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Name/description of the item in the image'
        },
        {
            'name': 'image_type',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'enum': ['food', 'ingredient', 'default'],
            'default': 'default',
            'description': 'Type/category of the image'
        }
    ],
    'responses': {
        201: {
            'description': 'Image uploaded successfully',
            'examples': {
                'application/json': {
                    'message': 'Image uploaded successfully',
                    'image': {
                        'uid': 'abc123...',
                        'name': 'banana',
                        'image_path': 'https://storage.googleapis.com/...',
                        'image_type': 'food',
                        'storage_path': 'uploads/food/abc123.jpg'
                    }
                }
            }
        },
        400: {'description': 'Invalid file or missing required fields'},
        401: {'description': 'Unauthorized - Valid JWT token required'},
        409: {'description': 'Image with same name already exists'},
        500: {'description': 'Upload failed due to server error'}
    },
    'security': [{'Bearer': []}]
})
def upload_image():
    """Upload image - Clean Architecture implementation"""
    user_uid = get_jwt_identity()
    
    # 🔍 LOGGING DETALLADO - INFORMACIÓN DE REQUEST
    print(f"📤 [IMAGE UPLOAD] ===== UPLOAD REQUEST DETAILS =====")
    print(f"📤 [IMAGE UPLOAD] User: {user_uid}")
    print(f"📤 [IMAGE UPLOAD] Method: {request.method}")
    print(f"📤 [IMAGE UPLOAD] URL: {request.url}")
    print(f"📤 [IMAGE UPLOAD] Content-Type: {request.content_type}")
    print(f"📤 [IMAGE UPLOAD] Content-Length: {request.content_length}")
    
    # 🔍 LOGGING DE HEADERS (sin datos sensibles)
    print(f"📤 [IMAGE UPLOAD] Headers:")
    for header_name, header_value in request.headers:
        if header_name.lower() not in ['authorization', 'cookie']:
            print(f"📤 [IMAGE UPLOAD]   {header_name}: {header_value}")
    
    # 🔍 VERIFICAR FORMULARIO
    print(f"📤 [IMAGE UPLOAD] Form data received:")
    for key, value in request.form.items():
        print(f"📤 [IMAGE UPLOAD]   Form[{key}]: {value}")
    
    # 🔍 VERIFICAR ARCHIVOS
    print(f"📤 [IMAGE UPLOAD] Files received:")
    for key, file in request.files.items():
        print(f"📤 [IMAGE UPLOAD]   File[{key}]: {file.filename} (size: {file.content_length if hasattr(file, 'content_length') else 'unknown'})")
        print(f"📤 [IMAGE UPLOAD]   File[{key}] mimetype: {file.content_type}")
    
    try:
        # 🔍 VALIDACIÓN DETALLADA DE CAMPOS
        image_file = request.files.get('image')
        item_name = request.form.get('item_name', '')
        image_type = request.form.get('image_type', 'default')
        
        print(f"📤 [IMAGE UPLOAD] Extracted fields:")
        print(f"📤 [IMAGE UPLOAD]   image_file: {image_file}")
        print(f"📤 [IMAGE UPLOAD]   item_name: '{item_name}'")
        print(f"📤 [IMAGE UPLOAD]   image_type: '{image_type}'")
        
        # Validaciones específicas
        if not image_file:
            print(f"❌ [IMAGE UPLOAD] No image file provided")
            return jsonify({
                "error": "No se proporcionó archivo de imagen",
                "received_files": list(request.files.keys()),
                "expected_field": "image"
            }), 400
            
        if not item_name:
            print(f"❌ [IMAGE UPLOAD] No item_name provided")
            return jsonify({
                "error": "No se proporcionó item_name",
                "received_form_data": dict(request.form),
                "expected_field": "item_name"
            }), 400
        
        if image_file.filename == '':
            print(f"❌ [IMAGE UPLOAD] Empty filename")
            return jsonify({
                "error": "Archivo sin nombre",
                "filename": image_file.filename
            }), 400
        
        print(f"📤 [IMAGE UPLOAD] Creating UploadRequest object...")
        
        upload_request = UploadRequest(
            image_file=image_file,
            item_name=item_name,
            image_type=image_type,
            user_uid=user_uid
        )
        
        print(f"✅ [IMAGE UPLOAD] UploadRequest created successfully")
        print(f"📤 [IMAGE UPLOAD] Starting upload process...")
        
        use_case = make_upload_image_use_case(db)
        result = use_case.execute(upload_request)
        
        print(f"✅ [IMAGE UPLOAD] Upload completed successfully")
        print(f"📤 [IMAGE UPLOAD] Result: {result}")
        print(f"📤 [IMAGE UPLOAD] ===== UPLOAD COMPLETED =====")
        
        response_data = upload_response_schema.dump(result)
        return jsonify(response_data), 201
        
    except ValueError as e:
        print(f"❌ [IMAGE UPLOAD] ValueError: {str(e)}")
        print(f"❌ [IMAGE UPLOAD] Error type: {type(e).__name__}")
        return jsonify({
            "error": str(e),
            "error_type": "ValueError",
            "error_details": {
                "user_uid": user_uid,
                "image_file": str(request.files.get('image')),
                "item_name": request.form.get('item_name', ''),
                "image_type": request.form.get('image_type', 'default'),
                "content_type": request.content_type
            }
        }), 400
        
    except InvalidRequestDataException as e:
        print(f"❌ [IMAGE UPLOAD] InvalidRequestDataException: {str(e)}")
        print(f"❌ [IMAGE UPLOAD] Exception details: {e.details}")
        
        if e.details and 'existing_image' in e.details:
            return jsonify({
                "error": str(e),
                "existing_image": e.details['existing_image'],
                "error_type": "InvalidRequestDataException"
            }), 409
        
        return jsonify({
            "error": str(e),
            "error_type": "InvalidRequestDataException",
            "error_details": e.details if hasattr(e, 'details') else None
        }), 400
        
    except Exception as e:
        import traceback
        print(f"🚨 [IMAGE UPLOAD] Unexpected error: {str(e)}")
        print(f"🚨 [IMAGE UPLOAD] Exception type: {type(e).__name__}")
        print(f"🚨 [IMAGE UPLOAD] Exception args: {e.args}")
        print(f"🚨 [IMAGE UPLOAD] FULL TRACEBACK:")
        print(traceback.format_exc())
        
        # Información adicional del contexto
        print(f"🚨 [IMAGE UPLOAD] Context info:")
        print(f"🚨 [IMAGE UPLOAD]   User UID: {user_uid}")
        print(f"🚨 [IMAGE UPLOAD]   Files: {list(request.files.keys())}")
        print(f"🚨 [IMAGE UPLOAD]   Form: {dict(request.form)}")
        
        return jsonify({
            "error": "Failed to upload image",
            "details": str(e),
            "error_type": str(type(e).__name__),
            "error_details": {
                "user_uid": user_uid,
                "files_received": list(request.files.keys()),
                "form_data": dict(request.form),
                "content_type": request.content_type,
                "content_length": request.content_length
            },
            "traceback": traceback.format_exc().split('\n')[-10:]  # Últimas 10 líneas
        }), 500
