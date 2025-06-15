from src.domain.repositories.generation_repository import GenerationRepository
from src.domain.models.generation import Generation
from src.infrastructure.db.models.generation_orm import GenerationORM

from sqlalchemy import insert, select, update
from typing import List, Optional

class GenerationRepositoryImpl(GenerationRepository):
    def __init__(self, db):
        self.db = db

    def save(self, generation: Generation) -> str:
        try:
            existing = self.find_by_uid(generation.uid)

            if existing:
                stmt = update(GenerationORM).where(
                    GenerationORM.uid == generation.uid
                ).values(
                    user_uid=generation.user_uid,
                    generated_at=generation.generated_at,
                    raw_result=generation.raw_result,
                    generation_type=generation.generation_type,
                    recipes_ids=generation.recipes_ids,
                    is_validated=generation.is_validated,
                    validated_at=generation.validated_at
                )
                self.db.session.execute(stmt)
                print(f"✅ [GENERATION REPO] Updated generation: {generation.uid}")
            else:
                stmt = insert(GenerationORM).values(
                    uid=generation.uid,
                    user_uid=generation.user_uid,
                    generated_at=generation.generated_at,
                    raw_result=generation.raw_result,
                    generation_type=generation.generation_type,
                    recipes_ids=generation.recipes_ids,
                    is_validated=generation.is_validated,
                    validated_at=generation.validated_at
                )
                self.db.session.execute(stmt)
                print(f"✅ [GENERATION REPO] Inserted new generation: {generation.uid}")

            self.db.session.commit()
            return generation.uid

        except Exception as e:
            self.db.session.rollback()
            print(f"🚨 [GENERATION REPO] Error in save: {str(e)}")
            raise

    def find_by_user(self, user_uid: str) -> List[Generation]:
        stmt = select(GenerationORM).where(GenerationORM.user_uid == user_uid)
        result = self.db.session.execute(stmt)
        return [self._to_domain(row[0]) for row in result.fetchall()]

    def find_by_uid(self, generation_uid: str) -> Optional[Generation]:
        stmt = select(GenerationORM).where(GenerationORM.uid == generation_uid)
        result = self.db.session.execute(stmt)
        row = result.fetchone()
        return self._to_domain(row[0]) if row else None

    def update_validation_status(self, generation_uid: str, validated: bool) -> None:
        stmt = update(GenerationORM).where(
            GenerationORM.uid == generation_uid
        ).values(
            is_validated=validated
        )
        self.db.session.execute(stmt)
        self.db.session.commit()

    def _to_domain(self, row: GenerationORM) -> Generation:
        return Generation(
            uid=row.uid,
            user_uid=row.user_uid,
            generated_at=row.generated_at,
            raw_result=row.raw_result,
            generation_type=row.generation_type,
            recipes_ids=row.recipes_ids,
            is_validated=row.is_validated,
            validated_at=row.validated_at
        )
