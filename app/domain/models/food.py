from pydantic import BaseModel
from typing import List, Optional

class Food(BaseModel):
    name: str
    main_ingredients: List[str]
    category: str
    calories: Optional[int]  # a veces puede ser None
    description: str
    storage_type: str
    expiration_time: int
    time_unit: str
    serving_quantity: int
    tips: str