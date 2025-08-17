from typing import List, Dict, Any
from datetime import datetime
from src.domain.models.cooking_session import StepConsumption
from src.infrastructure.db.cooking_session_repository_impl import CookingSessionRepository
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository
from src.shared.exceptions.custom import RecipeNotFoundException
from src.infrastructure.db.base import db

class CompleteStepUseCase:
    def __init__(
        self,
        cooking_session_repository: CookingSessionRepository,
        batch_repository: IngredientBatchRepository
    ):
        self.cooking_session_repository = cooking_session_repository
        self.batch_repository = batch_repository

    def execute(
        self,
        session_id: str,
        step_id: str,
        user_uid: str,
        timer_ms: int = None,
        consumptions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete a cooking step with ingredient consumptions.
        
        This operation is atomic and uses database transactions with locking
        to prevent race conditions on ingredient batches.
        
        Args:
            session_id: ID of the cooking session
            step_id: ID of the step being completed
            user_uid: UID of the user (for verification)
            timer_ms: Time taken for the step in milliseconds
            consumptions: List of ingredient consumptions
            
        Returns:
            Dict with completion status and inventory updates
            
        Raises:
            RecipeNotFoundException: If session is not found
            ValueError: For invalid inputs or insufficient ingredients
        """
        if not consumptions:
            consumptions = []
        
        # Start transaction
        try:
            with db.session.begin():
                # Get and verify session
                session = self.cooking_session_repository.find_by_id(session_id)
                if not session:
                    raise RecipeNotFoundException(f"Cooking session {session_id} not found")
                
                if session.user_uid != user_uid:
                    raise ValueError("Session does not belong to user")
                
                if not session.is_running():
                    raise ValueError("Session is not active")
                
                # Process each consumption with locking
                step_consumptions = []
                inventory_updates = []
                
                for consumption_data in consumptions:
                    ingredient_uid = consumption_data["ingredient_uid"]
                    lot_id = consumption_data["lot_id"]
                    qty = consumption_data["qty"]
                    unit = consumption_data["unit"]
                    
                    # Lock the batch for update to prevent race conditions
                    batch = self.batch_repository.lock_batch_for_update(lot_id)
                    if not batch:
                        raise ValueError(f"Batch {lot_id} not found")
                    
                    # Verify batch belongs to user
                    if batch.user_uid != user_uid:
                        raise ValueError(f"Batch {lot_id} does not belong to user")
                    
                    # Verify sufficient quantity and can be consumed
                    current_time = datetime.utcnow()
                    if not batch.can_be_consumed(current_time):
                        raise ValueError(f"Batch {lot_id} cannot be consumed (state: {batch.state})")
                    
                    if batch.qty < qty:
                        raise ValueError(f"Insufficient quantity in batch {lot_id}. Available: {batch.qty}, required: {qty}")
                    
                    # Consume from batch
                    batch.consume_quantity(qty)
                    
                    # Save updated batch
                    updated_batch = self.batch_repository.save(batch)
                    
                    # Create consumption record
                    consumption = StepConsumption(
                        ingredient_uid=ingredient_uid,
                        lot_id=lot_id,
                        qty=qty,
                        unit=unit
                    )
                    step_consumptions.append(consumption)
                    
                    # Log consumption for tracking
                    self.cooking_session_repository.log_consumption(
                        session_id=session_id,
                        step_id=step_id,
                        consumption=consumption,
                        user_uid=user_uid
                    )
                    
                    # Track inventory update
                    inventory_updates.append({
                        "lot_id": lot_id,
                        "new_qty": updated_batch.qty
                    })
                
                # Complete the step in the session
                session.complete_step(
                    step_id=step_id,
                    timer_ms=timer_ms,
                    consumptions=step_consumptions
                )
                
                # Save updated session
                self.cooking_session_repository.save(session)
                
                return {
                    "ok": True,
                    "inventory_updates": inventory_updates,
                    "step_completed_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            db.session.rollback()
            raise e