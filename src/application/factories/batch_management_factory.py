from src.application.use_cases.inventory.get_expiring_soon_batches_use_case import GetExpiringSoonBatchesUseCase
from src.application.use_cases.inventory.batch_management_use_cases import (
    ReserveBatchUseCase, FreezeBatchUseCase, TransformBatchUseCase, 
    QuarantineBatchUseCase, DiscardBatchUseCase
)
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository
from src.infrastructure.db.waste_log_repository_impl import WasteLogRepository
from src.infrastructure.db.base import db

def make_ingredient_batch_repository():
    return IngredientBatchRepository(db)

def make_waste_log_repository():
    return WasteLogRepository(db)

def make_get_expiring_soon_batches_use_case():
    batch_repository = make_ingredient_batch_repository()
    return GetExpiringSoonBatchesUseCase(batch_repository)

def make_reserve_batch_use_case():
    batch_repository = make_ingredient_batch_repository()
    return ReserveBatchUseCase(batch_repository)

def make_freeze_batch_use_case():
    batch_repository = make_ingredient_batch_repository()
    return FreezeBatchUseCase(batch_repository)

def make_transform_batch_use_case():
    batch_repository = make_ingredient_batch_repository()
    return TransformBatchUseCase(batch_repository)

def make_quarantine_batch_use_case():
    batch_repository = make_ingredient_batch_repository()
    return QuarantineBatchUseCase(batch_repository)

def make_discard_batch_use_case():
    batch_repository = make_ingredient_batch_repository()
    waste_log_repository = make_waste_log_repository()
    return DiscardBatchUseCase(batch_repository, waste_log_repository)