from typing import Optional, Dict, Any
from datetime import datetime, date
from src.infrastructure.db.cooking_session_repository_impl import CookingSessionRepository
from src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_uid import EstimateEnvironmentalSavingsFromRecipeUID
from src.shared.exceptions.custom import RecipeNotFoundException

class FinishCookingSessionUseCase:
    def __init__(
        self,
        cooking_session_repository: CookingSessionRepository,
        environmental_savings_use_case: EstimateEnvironmentalSavingsFromRecipeUID
    ):
        self.cooking_session_repository = cooking_session_repository
        self.environmental_savings_use_case = environmental_savings_use_case

    def execute(
        self,
        session_id: str,
        user_uid: str,
        notes: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Finish a cooking session and calculate environmental impact.
        
        Args:
            session_id: ID of the cooking session
            user_uid: UID of the user (for verification)
            notes: Optional notes about the cooking session
            photo_url: Optional photo URL of the finished dish
            
        Returns:
            Dict with session completion info, environmental savings, and leftover suggestions
            
        Raises:
            RecipeNotFoundException: If session is not found
            ValueError: For invalid session state
        """
        # Get and verify session
        session = self.cooking_session_repository.find_by_id(session_id)
        if not session:
            raise RecipeNotFoundException(f"Cooking session {session_id} not found")
        
        if session.user_uid != user_uid:
            raise ValueError("Session does not belong to user")
        
        if not session.is_running():
            raise ValueError("Session is already finished")
        
        # Finish the session
        session.finish_session(notes=notes, photo_url=photo_url)
        
        # Save updated session
        updated_session = self.cooking_session_repository.save(session)
        
        # Calculate environmental savings based on actual consumptions
        environmental_saving = None
        try:
            # Get actual consumptions from the session
            actual_consumptions = session.get_all_consumptions()
            
            # Calculate environmental impact (simplified - could be enhanced)
            if actual_consumptions:
                # For now, use the recipe-based calculation
                # In a full implementation, this would use actual consumption data
                environmental_result = self.environmental_savings_use_case.execute(
                    recipe_uid=session.recipe_uid
                )
                
                environmental_saving = {
                    "co2e_kg": environmental_result.get("co2_reduction_kg", 0),
                    "water_l": environmental_result.get("water_saved_liters", 0),
                    "waste_kg": environmental_result.get("food_waste_reduced_kg", 0)
                }
        except Exception as e:
            # Don't fail session completion if environmental calculation fails
            print(f"Environmental calculation failed: {e}")
            environmental_saving = {
                "co2e_kg": 0.0,
                "water_l": 0.0,
                "waste_kg": 0.0
            }
        
        # Generate leftover suggestion
        leftover_suggestion = self._generate_leftover_suggestion(session)
        
        return {
            "ok": True,
            "session_id": session_id,
            "finished_at": updated_session.finished_at.isoformat(),
            "total_cooking_time_ms": updated_session.get_total_cooking_time(),
            "environmental_saving": environmental_saving,
            "leftover_suggestion": leftover_suggestion
        }

    def _generate_leftover_suggestion(self, session) -> Optional[Dict[str, Any]]:
        """Generate suggestion for leftovers based on servings"""
        # Simple heuristic: if cooking for more than 2 people, suggest leftovers
        if session.servings > 2:
            suggested_portions = max(1, session.servings - 2)
            eat_by = date.today().replace(day=date.today().day + 2)  # 2 days from now
            
            return {
                "portions": suggested_portions,
                "eat_by": eat_by.isoformat()
            }
        
        return None