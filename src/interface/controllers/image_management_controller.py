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
    try:
        upload_request = UploadRequest(
            image_file=request.files.get('image'),
            item_name=request.form.get('item_name', ''),
            image_type=request.form.get('image_type', 'default'),
            user_uid=get_jwt_identity()
        )
        
        use_case = make_upload_image_use_case(db)
        result = use_case.execute(upload_request)
        
        return jsonify(upload_response_schema.dump(result)), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        
    except InvalidRequestDataException as e:
        if e.details and 'existing_image' in e.details:
            return jsonify({
                "error": str(e),
                "existing_image": e.details['existing_image']
            }), 409
        
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        return jsonify({
            "error": "Failed to upload image",
            "details": str(e)
        }), 500
