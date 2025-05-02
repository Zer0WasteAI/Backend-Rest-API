from src.domain.repositories.recognition_repository import RecognitionRepository
from src.domain.models.recognition import Recognition
from src.infrastructure.db.models.recognition_model import RecognitionORM

from sqlalchemy import insert, select, update
from typing import List, Optional

class RecognitionRepositoryImpl(RecognitionRepository):
    def __init__(self, db):
        self.db = db

    def save(self, recognition: Recognition) -> str:
        stmt = insert(RecognitionORM).values(
            uid=recognition.uid,
            user_uid=recognition.user_uid,
            image_path=recognition.image_path,
            images_paths=recognition.images_paths,
            recognized_at=recognition.recognized_at,
            raw_result=recognition.raw_result,
            is_validated=recognition.is_validated,
            validated_at=recognition.validated_at
        )

        self.db.session.execute(stmt)
        self.db.session.commit()
        return recognition.uid

    def find_by_user(self, user_uid: str) -> List[Recognition]:
        stmt = select(RecognitionORM).where(RecognitionORM.user_uid==user_uid)
        result = self.db.session.execute(stmt)
        return [self._to_domain(row[0]) for row in result.fetchall()]

    def find_by_uid(self, recognition_uid: str) -> Optional[Recognition]:
        stmt = select(RecognitionORM).where(RecognitionORM.uid==recognition_uid)
        result = self.db.session.execute(stmt)
        return self._to_domain(result[0]) if result[0] else None

    def update_validation_status(self, recognition_uid: str, validated: bool) -> None:
        stmt = update(RecognitionORM).where(RecognitionORM.uid==recognition_uid).values(
            is_validated=validated
        )
        self.db.session.execute(stmt)
        self.db.session.commit()

    def _to_domain(self, row) -> Recognition:
        return Recognition(
            uid=row.uid,
            user_uid=row.user_uid,
            image_path=row.image_path,
            images_paths=row.images_paths,
            recognized_at=row.recognized_at,
            raw_result=row.raw_result,
            is_validated=row.is_validated,
            validated_at=row.validated_at
        )