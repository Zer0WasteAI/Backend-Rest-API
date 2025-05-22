from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.infrastructure.db.base import db
from src.interface.serializers.image_reference_serializer import ImageReferencePublicSchema
from src.interface.serializers.item_name_serializer import ItemNameSchema
from src.application.factories.image_management_usecase_factory import (
    make_search_similar_images_use_case,
    make_assign_image_reference_use_case,
    make_sync_image_loader_use_case
)
from src.shared.exceptions.custom import InvalidRequestDataException
from src.shared.decorators.internal_only import internal_only

image_management_bp = Blueprint('image_management', __name__)
public_schema = ImageReferencePublicSchema()
item_name_schema = ItemNameSchema()

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

#TODO: Register in db image already uploaded
@image_management_bp.route("/sync_images", methods=["POST"])
@internal_only
def sync_images():
    use_case = make_sync_image_loader_use_case(db)
    added = use_case.execute()
    return jsonify({"message": f"{added} imágenes sincronizadas"}), 200

#TODO: Upload image with image

#TODO: Se podrán mapear todas las imágenes de firebase y guardarlas en la db con todo y ruta? :')