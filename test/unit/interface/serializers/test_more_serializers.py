import pytest
from datetime import date


def test_planning_save_meal_plan_request_schema():
    from src.interface.serializers.planning_serializers import SaveMealPlanRequestSchema
    schema = SaveMealPlanRequestSchema()
    payload = {
        'date': date.today().isoformat(),
        'meals': [
            {
                'title': 'T', 'duration': '10m', 'difficulty': 'Fácil',
                'ingredients': [{"name": "Tomate", "quantity": 1, "type_unit": "pcs"}],
                'steps': [{"step_order": 1, "description": "Paso"}],
                'generated_by_ai': True,
                'category': 'ensalada',
                'description': 'desc'
            }
        ]
    }
    ok = schema.load(payload)
    assert ok['meals'][0]['title'] == 'T'
    with pytest.raises(Exception):
        schema.load({'date': date.today().isoformat(), 'meals': []})


def test_upload_image_request_schema():
    from src.interface.serializers.upload_image_serializer import UploadImageRequestSchema
    schema = UploadImageRequestSchema()
    ok = schema.load({'item_name': 'tomato', 'image_type': 'ingredient'})
    assert ok['item_name'] == 'tomato'
    with pytest.raises(Exception):
        schema.load({'item_name': '!!'})


def test_item_name_schema_and_image_reference_schema():
    from src.interface.serializers.item_name_serializer import ItemNameSchema
    from src.interface.serializers.image_reference_serializer import ImageReferencePublicSchema
    name_schema = ItemNameSchema()
    img_schema = ImageReferencePublicSchema()
    assert name_schema.load({'item_name': 'tomato'})['item_name'] == 'tomato'
    img = img_schema.load({'name': 'tomato', 'image_path': 'http://x', 'image_type': 'ingredient'})
    assert img['image_type'] == 'ingredient'


def test_reset_password_serializers():
    from src.interface.serializers.reset_password_serializer import (
        SendPasswordResetCodeSchema, VerifyPasswordResetCodeSchema, ChangePasswordSchema
    )
    send = SendPasswordResetCodeSchema()
    verify = VerifyPasswordResetCodeSchema()
    change = ChangePasswordSchema()
    assert send.load({'email': 'a@b.com'})['email'] == 'a@b.com'
    assert verify.load({'email': 'a@b.com', 'code': '123456'})['code'] == '123456'
    with pytest.raises(Exception):
        verify.load({'email': 'a@b.com', 'code': '123'})
    assert change.load({'email': 'a@b.com', 'new_password': 'secret1'})['new_password'] == 'secret1'

