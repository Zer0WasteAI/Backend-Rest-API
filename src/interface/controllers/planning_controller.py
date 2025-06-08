from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.interface.serializers.planning_serializers import SaveMealPlanRequestSchema, MealPlanSchema
from src.application.factories.planning_usecase_factory import (
    make_save_meal_plan_use_case,
    make_update_meal_plan_use_case,
    make_delete_meal_plan_use_case,
    make_get_meal_plan_by_date_use_case,
    make_get_all_meal_plans_use_case,
    make_get_meal_plan_dates_use_case,
)
from src.shared.exceptions.custom import InvalidRequestDataException

planning_bp = Blueprint("planning", __name__)

@planning_bp.route("/save", methods=["POST"])
@jwt_required()
def save_meal_plan():
    user_uid = get_jwt_identity()
    schema = SaveMealPlanRequestSchema()
    json_data = request.get_json()

    try:
        data = schema.load(json_data)
    except Exception as err:
        raise InvalidRequestDataException(details=str(err))

    use_case = make_save_meal_plan_use_case()
    saved_plan = use_case.execute(
        user_uid=user_uid,
        plan_date=data["date"],
        meals=data["meals"]
    )

    result = MealPlanSchema().dump(saved_plan)
    return jsonify({
        "message": "Plan de comidas guardado exitosamente",
        "meal_plan": result
    }), 201


@planning_bp.route("/update", methods=["PUT"])
@jwt_required()
def update_meal_plan():
    user_uid = get_jwt_identity()
    schema = SaveMealPlanRequestSchema()
    json_data = request.get_json()

    try:
        data = schema.load(json_data)
    except Exception as err:
        raise InvalidRequestDataException(details=str(err))

    use_case = make_update_meal_plan_use_case()
    updated_plan = use_case.execute(
        user_uid=user_uid,
        plan_date=data["date"],
        meals=data["meals"]
    )

    result = MealPlanSchema().dump(updated_plan)
    return jsonify({
        "message": "Plan de comidas actualizado exitosamente",
        "meal_plan": result
    })


@planning_bp.route("/delete", methods=["DELETE"])
@jwt_required()
def delete_meal_plan():
    user_uid = get_jwt_identity()
    date_str = request.args.get("date")

    if not date_str:
        raise InvalidRequestDataException("Se requiere el parámetro 'date'.")

    try:
        plan_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidRequestDataException("El formato de la fecha debe ser YYYY-MM-DD.")

    use_case = make_delete_meal_plan_use_case()
    use_case.execute(user_uid=user_uid, plan_date=plan_date)

    return jsonify({"message": f"Plan de comidas del {plan_date} eliminado exitosamente."})


@planning_bp.route("/get", methods=["GET"])
@jwt_required()
def get_meal_plan_by_date():
    user_uid = get_jwt_identity()
    date_str = request.args.get("date")

    if not date_str:
        raise InvalidRequestDataException("Se requiere el parámetro 'date'.")

    try:
        plan_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidRequestDataException("El formato de la fecha debe ser YYYY-MM-DD.")

    use_case = make_get_meal_plan_by_date_use_case()
    plan = use_case.execute(user_uid=user_uid, plan_date=plan_date)

    result = MealPlanSchema().dump(plan)
    return jsonify({"meal_plan": result})


@planning_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_meal_plans():
    user_uid = get_jwt_identity()
    use_case = make_get_all_meal_plans_use_case()
    plans = use_case.execute(user_uid=user_uid)

    result = MealPlanSchema(many=True).dump(plans)
    return jsonify({"meal_plans": result})


@planning_bp.route("/dates", methods=["GET"])
@jwt_required()
def get_meal_plan_dates():
    user_uid = get_jwt_identity()
    use_case = make_get_meal_plan_dates_use_case()
    dates = use_case.execute(user_uid=user_uid)

    return jsonify({"dates": [d.isoformat() for d in dates]})
