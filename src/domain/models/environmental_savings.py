from sqlalchemy import false


class EnvironmentalSavings:
    def __init__(self, user_uid, recipe_uid, recipe_title, carbon_footprint, water_footprint, energy_footprint,
                 economic_cost, unit_carbon, unit_water, unit_energy, unit_cost, is_cooked: bool = False, 
                 recipe_source_type: str = "manual", saved_at=None):
        self.user_uid = user_uid
        self.recipe_uid = recipe_uid
        self.recipe_source_type = recipe_source_type  # 'manual' or 'generated'
        self.recipe_title = recipe_title
        self.carbon_footprint = carbon_footprint
        self.water_footprint = water_footprint
        self.energy_footprint = energy_footprint
        self.economic_cost = economic_cost
        self.unit_carbon = unit_carbon
        self.unit_water = unit_water
        self.unit_energy = unit_energy
        self.unit_cost = unit_cost
        self.is_cooked = is_cooked
        self.saved_at = saved_at
