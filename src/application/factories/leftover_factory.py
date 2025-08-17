from src.application.use_cases.inventory.create_leftover_use_case import CreateLeftoverUseCase
from src.infrastructure.db.leftover_repository_impl import LeftoverRepository
from src.infrastructure.db.base import db

def make_leftover_repository():
    return LeftoverRepository(db)

def make_create_leftover_use_case():
    leftover_repository = make_leftover_repository()
    return CreateLeftoverUseCase(leftover_repository)