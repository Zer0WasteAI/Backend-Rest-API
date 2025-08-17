import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from src.application.use_cases.inventory.upload_inventory_image_use_case import UploadInventoryImageUseCase
from src.application.use_cases.inventory.add_ingredients_and_foods_to_inventory_use_case import AddIngredientsAndFoodsToInventoryUseCase
from src.application.use_cases.inventory.update_ingredient_stack_use_case import UpdateIngredientStackUseCase
from src.application.use_cases.inventory.get_expiring_soon_batches_use_case import GetExpiringSoonBatchesUseCase


class TestUploadInventoryImageUseCase:
    def test_execute_happy_path(self):
        validator = MagicMock()
        uploader = MagicMock()
        uploader.INVENTORY_UPLOAD_TYPES = {'ingredient': 'ingredients'}
        uploader.upload_inventory_image.return_value = ('path/img.jpg', 'http://public/img.jpg')
        uc = UploadInventoryImageUseCase(validator, uploader)

        file = SimpleNamespace(filename='img.jpg')
        result = uc.execute(file=file, upload_type='ingredient', user_uid='u1', item_name='tomato')
        validator.validate_inventory_upload.assert_called_once()
        uploader.upload_inventory_image.assert_called_once()
        assert result['upload_info']['public_url'].endswith('img.jpg')


class TestAddIngredientsAndFoodsToInventoryUseCase:
    def test_execute_with_precalculated_expirations(self):
        repo = MagicMock()
        calc = MagicMock()
        inv = MagicMock()
        repo.get_by_user_uid.return_value = inv
        uc = AddIngredientsAndFoodsToInventoryUseCase(repo, calc)
        ingredients = [{
            'name': 'Tomato', 'quantity': 1, 'type_unit': 'pcs', 'storage_type': 'fridge',
            'tips': '', 'image_path': '', 'expiration_date': '2024-01-02T00:00:00Z'
        }]
        foods = [{
            'name': 'Pizza', 'main_ingredients': [], 'category': 'prepared', 'calories': 800,
            'description': '', 'storage_type': 'fridge', 'tips': '', 'serving_quantity': 2,
            'image_path': '', 'expiration_date': '2024-01-02T00:00:00Z'
        }]
        uc.execute('u1', ingredients, foods)
        assert repo.update.called

    def test_execute_raises_on_missing_expiration_info(self):
        repo = MagicMock()
        calc = MagicMock()
        inv = MagicMock()
        repo.get_by_user_uid.return_value = inv
        uc = AddIngredientsAndFoodsToInventoryUseCase(repo, calc)
        with pytest.raises(ValueError):
            uc.execute('u1', [{'name': 'X', 'quantity': 1, 'type_unit': 'g', 'storage_type': 'fridge', 'tips': '', 'image_path': ''}], [])


class TestUpdateIngredientStackUseCase:
    def test_execute_with_precalculated_expiration(self):
        repo = MagicMock()
        calc = MagicMock()
        uc = UpdateIngredientStackUseCase(repo, calc)
        updated = {
            'quantity': 2, 'type_unit': 'g', 'added_at': '2024-01-01T00:00:00Z',
            'expiration_date': '2024-01-03T00:00:00Z', 'storage_type': 'fridge', 'tips': '', 'image_path': ''
        }
        uc.execute('u', 'Tomato', '2024-01-01T00:00:00Z', updated)
        assert repo.update_ingredient_stack.called

    def test_execute_with_calculated_expiration(self):
        repo = MagicMock()
        calc = MagicMock()
        calc.calculate_expiration_date.return_value = SimpleNamespace()
        uc = UpdateIngredientStackUseCase(repo, calc)
        updated = {
            'quantity': 2, 'type_unit': 'g', 'added_at': '2024-01-01T00:00:00Z',
            'expiration_time': 3, 'time_unit': 'days', 'storage_type': 'fridge', 'tips': '', 'image_path': ''
        }
        uc.execute('u', 'Tomato', '2024-01-01T00:00:00Z', updated)
        assert repo.update_ingredient_stack.called

    def test_execute_missing_expiration_info_raises(self):
        repo = MagicMock()
        calc = MagicMock()
        uc = UpdateIngredientStackUseCase(repo, calc)
        with pytest.raises(ValueError):
            uc.execute('u', 'Tomato', '2024-01-01T00:00:00Z', {'quantity': 1, 'type_unit': 'g', 'added_at': '2024-01-01T00:00:00Z'})


class TestGetExpiringSoonBatchesUseCase:
    def test_execute_returns_formatted_batches(self):
        repo = MagicMock()
        # Mock batch with necessary attributes
        batch = MagicMock()
        batch.id = 'b1'
        batch.ingredient_uid = 'ing_tomato'
        batch.qty = 100
        batch.unit = 'g'
        batch.expiry_date = SimpleNamespace(isoformat=lambda: '2024-01-02T00:00:00Z')
        batch.storage_location.value = 'fridge'
        batch.label_type.value = 'use_by'
        batch.state.value = 'available'
        batch.created_at = SimpleNamespace(__sub__=lambda self, other=None: SimpleNamespace(days=1))
        batch.calculate_urgency_score.return_value = 0.95
        repo.find_expiring_soon.return_value = [batch]
        uc = GetExpiringSoonBatchesUseCase(repo)
        res = uc.execute('u1', within_days=3)
        assert isinstance(res, list) and res
        assert res[0]['batch_id'] == 'b1'

