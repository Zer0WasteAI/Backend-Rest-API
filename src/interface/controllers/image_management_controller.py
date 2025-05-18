from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.infrastructure.db.base import db
from src.interface.serializers.image_reference_serializer import ImageReferencePublicSchema
from src.interface.serializers.item_name_serializer import ItemNameSchema
from src.application.factories.image_management_usecase_factory import (
    make_search_similar_images_use_case,
    make_assign_image_reference_use_case
)
from src.shared.exceptions.custom import InvalidRequestDataException

image_management_bp = Blueprint('image_management', __name__)
public_schema = ImageReferencePublicSchema()
item_name_schema = ItemNameSchema()

@image_management_bp.route("/assign_image", methods=["GET"])
@jwt_required
def assign_image():
    errors = item_name_schema.validate(request.args)
    if errors:
        raise InvalidRequestDataException(details=errors)

    item_name = request.args.get("item_name")
    use_case = make_assign_image_reference_use_case(db)
    result = use_case.execute(similar_name=item_name)

    serialized = public_schema.dump(result)
    return jsonify(serialized), 200

@image_management_bp.route("/search_similar_images", methods=["GET"])
@jwt_required()
def search_similar_images():
    errors = item_name_schema.validate(request.args)
    if errors:
        return jsonify(errors), 400

    item_name = request.args.get("item_name")
    use_case = make_search_similar_images_use_case(db)
    results = use_case.execute(similar_name=item_name)

    serialized_list = public_schema.dump(results, many=True)
    return jsonify(serialized_list), 200

#TODO: Register in db image already uploaded

#TODO: Upload image with image

#TODO: Se podrán mapear todas las imágenes de firebase y guardarlas en la db con todo y ruta? :')