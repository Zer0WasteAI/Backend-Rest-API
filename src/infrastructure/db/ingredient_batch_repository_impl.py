from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, desc, asc
from src.domain.models.ingredient_batch import IngredientBatch, BatchState, LabelType, StorageLocation
from src.infrastructure.db.models.ingredient_batch_orm import IngredientBatchORM
from src.infrastructure.db.base import db
import uuid

class IngredientBatchRepository:
    def __init__(self, database=None):
        self.db = database or db

    def save(self, batch: IngredientBatch) -> IngredientBatch:
        """Save or update an ingredient batch"""
        batch_orm = self.db.session.get(IngredientBatchORM, batch.id)
        
        if batch_orm:
            # Update existing
            batch_orm.qty = batch.qty
            batch_orm.state = batch.state
            batch_orm.storage_location = batch.storage_location
            batch_orm.sealed = batch.sealed
            batch_orm.updated_at = datetime.utcnow()
        else:
            # Create new
            if not batch.id:
                batch.id = str(uuid.uuid4())
                
            batch_orm = IngredientBatchORM(
                id=batch.id,
                ingredient_uid=batch.ingredient_uid,
                qty=batch.qty,
                unit=batch.unit,
                storage_location=batch.storage_location,
                label_type=batch.label_type,
                expiry_date=batch.expiry_date,
                state=batch.state,
                sealed=batch.sealed,
                user_uid=getattr(batch, 'user_uid', ''),  # Should be set by use case
                created_at=batch.created_at,
                updated_at=batch.updated_at
            )
            self.db.session.add(batch_orm)
        
        self.db.session.commit()
        return self._map_to_domain(batch_orm)

    def find_by_id(self, batch_id: str) -> Optional[IngredientBatch]:
        """Find batch by ID"""
        batch_orm = self.db.session.get(IngredientBatchORM, batch_id)
        return self._map_to_domain(batch_orm) if batch_orm else None

    def find_by_ingredient_fefo(self, ingredient_uid: str, user_uid: str, required_qty: float) -> List[IngredientBatch]:
        """Find batches for ingredient using FEFO (First Expired, First Out)"""
        batch_orms = (
            self.db.session.query(IngredientBatchORM)
            .filter(
                and_(
                    IngredientBatchORM.ingredient_uid == ingredient_uid,
                    IngredientBatchORM.user_uid == user_uid,
                    IngredientBatchORM.state.in_([BatchState.AVAILABLE, BatchState.RESERVED]),
                    IngredientBatchORM.qty > 0
                )
            )
            .order_by(asc(IngredientBatchORM.expiry_date))
            .all()
        )
        
        # Filter out expired use_by items
        current_time = datetime.utcnow()
        valid_batches = []
        
        for batch_orm in batch_orms:
            batch = self._map_to_domain(batch_orm)
            if batch.can_be_consumed(current_time):
                valid_batches.append(batch)
        
        return valid_batches

    def find_expiring_soon(self, user_uid: str, within_days: int = 3, storage: Optional[str] = None) -> List[IngredientBatch]:
        """Find batches expiring soon"""
        cutoff_date = datetime.utcnow() + timedelta(days=within_days)
        
        query_filters = [
            IngredientBatchORM.user_uid == user_uid,
            IngredientBatchORM.expiry_date <= cutoff_date,
            IngredientBatchORM.state.in_([BatchState.AVAILABLE, BatchState.RESERVED, BatchState.EXPIRING_SOON])
        ]
        
        if storage:
            try:
                storage_location = StorageLocation(storage)
                query_filters.append(IngredientBatchORM.storage_location == storage_location)
            except ValueError:
                pass  # Invalid storage location, ignore filter
        
        batch_orms = (
            self.db.session.query(IngredientBatchORM)
            .filter(and_(*query_filters))
            .order_by(asc(IngredientBatchORM.expiry_date))
            .all()
        )
        
        # Calculate urgency scores and sort
        batches_with_urgency = []
        current_time = datetime.utcnow()
        
        for batch_orm in batch_orms:
            batch = self._map_to_domain(batch_orm)
            urgency_score = batch.calculate_urgency_score(current_time)
            batches_with_urgency.append((batch, urgency_score))
        
        # Sort by urgency score (highest first)
        batches_with_urgency.sort(key=lambda x: x[1], reverse=True)
        
        return [batch for batch, _ in batches_with_urgency]

    def update_expired_batches(self) -> int:
        """Update batches that have expired (job function)"""
        current_time = datetime.utcnow()
        
        # Mark use_by items as expired
        use_by_expired = (
            self.db.session.query(IngredientBatchORM)
            .filter(
                and_(
                    IngredientBatchORM.label_type == LabelType.USE_BY,
                    IngredientBatchORM.expiry_date < current_time,
                    IngredientBatchORM.state.in_([BatchState.AVAILABLE, BatchState.RESERVED, BatchState.EXPIRING_SOON])
                )
            )
            .update({"state": BatchState.EXPIRED}, synchronize_session=False)
        )
        
        # Mark best_before items as quarantine (still usable but check quality)
        best_before_expired = (
            self.db.session.query(IngredientBatchORM)
            .filter(
                and_(
                    IngredientBatchORM.label_type == LabelType.BEST_BEFORE,
                    IngredientBatchORM.expiry_date < current_time,
                    IngredientBatchORM.state.in_([BatchState.AVAILABLE, BatchState.RESERVED, BatchState.EXPIRING_SOON])
                )
            )
            .update({"state": BatchState.QUARANTINE}, synchronize_session=False)
        )
        
        # Mark items expiring soon
        expiring_cutoff = current_time + timedelta(days=3)
        expiring_soon = (
            self.db.session.query(IngredientBatchORM)
            .filter(
                and_(
                    IngredientBatchORM.expiry_date <= expiring_cutoff,
                    IngredientBatchORM.expiry_date > current_time,
                    IngredientBatchORM.state == BatchState.AVAILABLE
                )
            )
            .update({"state": BatchState.EXPIRING_SOON}, synchronize_session=False)
        )
        
        self.db.session.commit()
        return use_by_expired + best_before_expired + expiring_soon

    def lock_batch_for_update(self, batch_id: str) -> Optional[IngredientBatch]:
        """Lock batch for update (for concurrency control)"""
        batch_orm = (
            self.db.session.query(IngredientBatchORM)
            .filter(IngredientBatchORM.id == batch_id)
            .with_for_update()
            .first()
        )
        return self._map_to_domain(batch_orm) if batch_orm else None

    def find_by_user(self, user_uid: str, state: Optional[BatchState] = None) -> List[IngredientBatch]:
        """Find all batches for a user, optionally filtered by state"""
        query = self.db.session.query(IngredientBatchORM).filter(
            IngredientBatchORM.user_uid == user_uid
        )
        
        if state:
            query = query.filter(IngredientBatchORM.state == state)
        
        batch_orms = query.order_by(asc(IngredientBatchORM.expiry_date)).all()
        return [self._map_to_domain(batch_orm) for batch_orm in batch_orms]

    def _map_to_domain(self, batch_orm: IngredientBatchORM) -> IngredientBatch:
        """Map ORM to domain model"""
        batch = IngredientBatch(
            id=batch_orm.id,
            ingredient_uid=batch_orm.ingredient_uid,
            qty=batch_orm.qty,
            unit=batch_orm.unit,
            storage_location=batch_orm.storage_location,
            label_type=batch_orm.label_type,
            expiry_date=batch_orm.expiry_date,
            state=batch_orm.state,
            sealed=batch_orm.sealed,
            created_at=batch_orm.created_at,
            updated_at=batch_orm.updated_at
        )
        # Add user_uid as an attribute for tracking
        batch.user_uid = batch_orm.user_uid
        return batch