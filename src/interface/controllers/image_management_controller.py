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
def sync_images():
    use_case = make_sync_image_loader_use_case(db)
    added = use_case.execute()
    return jsonify({"message": f"{added} imágenes sincronizadas"}), 200


@image_management_bp.route("/upload_image", methods=["POST"])
@jwt_required()
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
