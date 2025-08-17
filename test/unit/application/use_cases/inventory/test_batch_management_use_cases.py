import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.application.use_cases.inventory.batch_management_use_cases import (
    ReserveBatchUseCase, FreezeBatchUseCase, TransformBatchUseCase, QuarantineBatchUseCase, DiscardBatchUseCase
)
from src.domain.models.ingredient_batch import IngredientBatch, BatchState, LabelType, StorageLocation
from src.domain.models.waste_log import WasteReason


def make_batch(state=BatchState.AVAILABLE):
    b = IngredientBatch(
        id='b1', ingredient_uid='ing_tomato', qty=100, unit='g',
        storage_location=StorageLocation.FRIDGE, label_type=LabelType.USE_BY,
        expiry_date=datetime.now(), state=state
    )
    b.user_uid = 'u1'
    return b


class TestReserveBatchUseCase:
    def test_reserve_success(self):
        repo = MagicMock()
        batch = make_batch()
        repo.find_by_id.return_value = batch
        repo.save.return_value = batch
        uc = ReserveBatchUseCase(repo)
        res = uc.execute('b1', 'u1', '2024-01-10', 'lunch')
        assert res['batch_id'] == 'b1'


class TestFreezeBatchUseCase:
    def test_freeze_success(self):
        repo = MagicMock()
        batch = make_batch()
        repo.find_by_id.return_value = batch
        repo.save.return_value = batch
        uc = FreezeBatchUseCase(repo)
        res = uc.execute('b1', 'u1', datetime.now().isoformat())
        assert res['batch_id'] == 'b1'


class TestTransformBatchUseCase:
    def test_transform_success(self):
        repo = MagicMock()
        batch = make_batch()
        repo.find_by_id.return_value = batch
        repo.save.side_effect = [batch, make_batch()]  # original then new batch
        uc = TransformBatchUseCase(repo)
        res = uc.execute('b1', 'u1', 'sofrito', 50, 'g', datetime.now().isoformat())
        assert res['original_batch_id'] == 'b1'


class TestQuarantineBatchUseCase:
    def test_quarantine_success(self):
        repo = MagicMock()
        batch = make_batch()
        repo.find_by_id.return_value = batch
        repo.save.return_value = batch
        uc = QuarantineBatchUseCase(repo)
        res = uc.execute('b1', 'u1')
        assert res['batch_id'] == 'b1'


class TestDiscardBatchUseCase:
    def test_discard_success(self):
        batch_repo = MagicMock()
        waste_repo = MagicMock()
        batch = make_batch()
        batch_repo.find_by_id.return_value = batch
        waste_log = MagicMock()
        waste_log.waste_id = 'w1'
        waste_repo.save.return_value = waste_log
        uc = DiscardBatchUseCase(batch_repo, waste_repo)
        res = uc.execute('b1', 'u1', 100.0, 'g', WasteReason.EXPIRED.value)
        assert res['batch_id'] == 'b1'
        assert res['waste_id'] == 'w1'

