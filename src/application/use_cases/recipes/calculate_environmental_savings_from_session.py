from typing import List, Dict, Any
from src.infrastructure.db.cooking_session_repository_impl import CookingSessionRepository
from src.infrastructure.db.environmental_savings_repository_impl import EnvironmentalSavingsRepositoryImpl
from src.domain.models.environmental_savings import EnvironmentalSavings
from src.shared.exceptions.custom import RecipeNotFoundException
import uuid

class CalculateEnvironmentalSavingsFromSessionUseCase:
    def __init__(
        self,
        session_repository: CookingSessionRepository,
        environmental_repository: EnvironmentalSavingsRepositoryImpl
    ):
        self.session_repository = session_repository
        self.environmental_repository = environmental_repository

    def execute(self, session_id: str, user_uid: str, actual_consumptions: List[Dict[str, Any]] = None) -> dict:
        """
        Calculate environmental savings based on actual cooking session consumption.
        
        Args:
            session_id: ID of the cooking session
            user_uid: UID of the user (for verification)
            actual_consumptions: Optional list of actual consumptions (overrides session data)
            
        Returns:
            Dict with environmental impact metrics
        """
        # Get cooking session
        session = self.session_repository.find_by_id(session_id)
        if not session:
            raise RecipeNotFoundException(f"Cooking session {session_id} not found")
        
        if session.user_uid != user_uid:
            raise ValueError("Session does not belong to user")
        
        # Use provided consumptions or get from session
        if actual_consumptions:
            consumptions = actual_consumptions
        else:
            session_consumptions = session.get_all_consumptions()
            consumptions = [
                {
                    "ingredient_uid": c.ingredient_uid,
                    "qty": c.qty,
                    "unit": c.unit
                } for c in session_consumptions
            ]
        
        # Calculate environmental impact based on actual consumptions
        environmental_savings = self._calculate_savings(consumptions, session.servings)
        
        # Create environmental savings record
        savings_record = EnvironmentalSavings(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            recipe_uid=session.recipe_uid,
            co2_reduction_kg=environmental_savings["co2e_kg"],
            water_saved_liters=environmental_savings["water_l"],
            food_waste_reduced_kg=environmental_savings["waste_kg"],
            calculation_method="session_based",
            calculation_metadata={
                "session_id": session_id,
                "servings": session.servings,
                "consumption_count": len(consumptions),
                "basis": "per_session"
            }
        )
        
        # Save the calculation
        saved_savings = self.environmental_repository.save(savings_record)
        
        return {
            "calculation_id": saved_savings.uid,
            "session_id": session_id,
            "co2e_kg": environmental_savings["co2e_kg"],
            "water_l": environmental_savings["water_l"],
            "waste_kg": environmental_savings["waste_kg"],
            "basis": "per_session",
            "consumptions_analyzed": len(consumptions),
            "calculated_at": saved_savings.calculated_at.isoformat()
        }

    def _calculate_savings(self, consumptions: List[Dict[str, Any]], servings: int) -> Dict[str, float]:
        """
        Calculate environmental savings based on actual ingredient consumptions.
        
        This is a simplified calculation - in a real implementation,
        this would use detailed environmental factor databases.
        """
        total_co2_saved = 0.0
        total_water_saved = 0.0
        total_waste_reduced = 0.0
        
        # Environmental factors per ingredient type (simplified)
        environmental_factors = {
            # CO2 savings (kg per kg ingredient) vs. processed/restaurant alternatives
            "co2_factors": {
                "ing_chicken": 0.8,    # Home cooking vs processed chicken
                "ing_beef": 1.2,       # Home cooking vs processed beef
                "ing_vegetables": 0.3, # Fresh vs processed vegetables
                "ing_rice": 0.2,       # Bulk vs packaged rice
                "ing_pasta": 0.15,     # Bulk vs packaged pasta
                "default": 0.4         # Average factor
            },
            # Water savings (liters per kg ingredient) vs. processed alternatives
            "water_factors": {
                "ing_chicken": 50,     # Water saved in processing
                "ing_beef": 80,        # Water saved in processing
                "ing_vegetables": 20,  # Water saved vs processed vegetables
                "ing_rice": 10,        # Water saved in packaging
                "ing_pasta": 15,       # Water saved in packaging
                "default": 25          # Average factor
            },
            # Waste reduction (kg per kg ingredient) - food saved from waste
            "waste_factors": {
                "ing_chicken": 0.1,    # Better portion control
                "ing_beef": 0.15,      # Better portion control
                "ing_vegetables": 0.2, # Use of whole vegetables
                "ing_rice": 0.05,      # Exact portions
                "ing_pasta": 0.05,     # Exact portions
                "default": 0.1         # Average factor
            }
        }
        
        for consumption in consumptions:
            ingredient_uid = consumption["ingredient_uid"]
            qty = consumption["qty"]
            unit = consumption["unit"]
            
            # Convert quantity to kg for calculation
            qty_kg = self._convert_to_kg(qty, unit)
            
            # Get environmental factors for this ingredient
            co2_factor = environmental_factors["co2_factors"].get(
                ingredient_uid, 
                environmental_factors["co2_factors"]["default"]
            )
            water_factor = environmental_factors["water_factors"].get(
                ingredient_uid,
                environmental_factors["water_factors"]["default"]
            )
            waste_factor = environmental_factors["waste_factors"].get(
                ingredient_uid,
                environmental_factors["waste_factors"]["default"]
            )
            
            # Calculate savings for this ingredient
            total_co2_saved += qty_kg * co2_factor
            total_water_saved += qty_kg * water_factor
            total_waste_reduced += qty_kg * waste_factor
        
        # Apply servings multiplier (cooking for more people = more impact)
        servings_multiplier = max(1.0, servings / 2.0)  # Base assumption: 2 servings
        
        return {
            "co2e_kg": round(total_co2_saved * servings_multiplier, 3),
            "water_l": round(total_water_saved * servings_multiplier, 1),
            "waste_kg": round(total_waste_reduced * servings_multiplier, 3)
        }

    def _convert_to_kg(self, qty: float, unit: str) -> float:
        """Convert quantity to kg for calculation"""
        conversion_factors = {
            "kg": 1.0,
            "g": 0.001,
            "l": 1.0,      # Assume 1L = 1kg for liquids
            "ml": 0.001,   # Assume 1ml = 1g
            "units": 0.1,  # Assume 1 unit = 100g average
            "u": 0.1,      # Assume 1 unit = 100g average
        }
        
        factor = conversion_factors.get(unit.lower(), 0.1)  # Default 100g
        return qty * factor