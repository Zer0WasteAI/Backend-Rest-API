from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class PreheatInstruction:
    device: str
    setting: str
    duration_ms: int

@dataclass
class PrepTask:
    id: str
    text: str
    ingredient_uid: Optional[str] = None
    suggested_qty: Optional[float] = None
    unit: Optional[str] = None

@dataclass
class MeasuredIngredient:
    ingredient_uid: str
    qty: float
    unit: str
    lot_suggestion: Optional[str] = None

class MiseEnPlace:
    def __init__(
        self,
        recipe_uid: str,
        servings: int,
        tools: List[str],
        preheat: List[PreheatInstruction],
        prep_tasks: List[PrepTask],
        measured_ingredients: List[MeasuredIngredient]
    ):
        self.recipe_uid = recipe_uid
        self.servings = servings
        self.tools = tools
        self.preheat = preheat
        self.prep_tasks = prep_tasks
        self.measured_ingredients = measured_ingredients
        self._validate()

    def _validate(self):
        if self.servings <= 0:
            raise ValueError("Servings must be positive")
        if not self.recipe_uid:
            raise ValueError("Recipe UID is required")

    def scale_for_servings(self, base_servings: int):
        """Scale all quantities based on servings ratio"""
        if base_servings <= 0:
            raise ValueError("Base servings must be positive")
        
        scale_factor = self.servings / base_servings
        
        # Scale prep tasks quantities
        for task in self.prep_tasks:
            if task.suggested_qty:
                task.suggested_qty *= scale_factor
        
        # Scale measured ingredients
        for ingredient in self.measured_ingredients:
            ingredient.qty *= scale_factor

    def add_lot_suggestions(self, lot_suggestions: Dict[str, str]):
        """Add FEFO lot suggestions to measured ingredients"""
        for ingredient in self.measured_ingredients:
            if ingredient.ingredient_uid in lot_suggestions:
                ingredient.lot_suggestion = lot_suggestions[ingredient.ingredient_uid]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "recipe_uid": self.recipe_uid,
            "servings": self.servings,
            "tools": self.tools,
            "preheat": [
                {
                    "device": p.device,
                    "setting": p.setting,
                    "duration_ms": p.duration_ms
                } for p in self.preheat
            ],
            "prep_tasks": [
                {
                    "id": t.id,
                    "text": t.text,
                    "ingredient_uid": t.ingredient_uid,
                    "suggested_qty": t.suggested_qty,
                    "unit": t.unit
                } for t in self.prep_tasks
            ],
            "measured_ingredients": [
                {
                    "ingredient_uid": i.ingredient_uid,
                    "qty": i.qty,
                    "unit": i.unit,
                    "lot_suggestion": i.lot_suggestion
                } for i in self.measured_ingredients
            ]
        }

    def __repr__(self):
        return f"MiseEnPlace(recipe={self.recipe_uid}, servings={self.servings}, ingredients={len(self.measured_ingredients)})"