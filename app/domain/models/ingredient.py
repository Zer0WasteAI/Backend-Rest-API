from pydantic import BaseModel
from typing import List, Optional

class Ingredient(BaseModel):
    name: str
    quantity: int
    type_unit: str
    storage_type: str
    expiration_time: int
    time_unit: str
    tips: str