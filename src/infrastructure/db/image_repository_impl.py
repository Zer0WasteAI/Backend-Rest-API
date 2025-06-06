import unicodedata
from typing import List, Optional
from sqlalchemy import select
from src.domain.models.image_reference import ImageReference
from src.domain.repositories.image_repository import ImageReferenceRepository
from src.infrastructure.db.models.image_reference_orm import ImageReferenceORM


def normalize_name(name: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', name)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

class ImageRepositoryImpl(ImageReferenceRepository):
    def __init__(self, db):
        self.db = db

    def save(self, image: ImageReference) -> str:
        normalized_name = normalize_name(image.name)
        obj = ImageReferenceORM(
            uid=image.uid,
            name=normalized_name,
            image_path=image.image_path,
            image_type=image.image_type
        )
        self.db.session.add(obj)
        self.db.session.commit()
        return image.uid

    def find_by_uid(self, uid: str) -> Optional[ImageReference]:
        result = self.db.session.get(ImageReferenceORM, uid)
        return self._to_domain(result) if result else None

    def find_by_name(self, name: str) -> Optional[ImageReference]:
        normalized_name = normalize_name(name)
        stmt = select(ImageReferenceORM).where(
            self.db.func.lower(ImageReferenceORM.name) == normalized_name
        )
        result = self.db.session.execute(stmt).scalar_one_or_none()
        return self._to_domain(result) if result else None

    def find_best_match_name(self, name: str) -> Optional[List[ImageReference]]:
        normalized_name = normalize_name(name)
        stmt = select(ImageReferenceORM).where(
            self.db.func.lower(ImageReferenceORM.name).like(f"%{normalized_name}%")
        )
        results = self.db.session.execute(stmt).scalars().all()
        return [self._to_domain(result) for result in results] if results else None

    def _to_domain(self, row: ImageReferenceORM) -> ImageReference:
        return ImageReference(
            uid=row.uid,
            name=row.name,
            image_path=row.image_path,
            image_type=row.image_type
        )