from src.infrastructure.db.base import db
from src.infrastructure.db.generation_repository_impl import GenerationRepositoryImpl


def make_generation_repository():
    return GenerationRepositoryImpl(db)