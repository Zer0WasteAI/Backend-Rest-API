from marshmallow import Schema, fields, validate


class MarkIngredientConsumedSchema(Schema):
    """Schema para validar marcar ingrediente como consumido"""
    
    consumed_quantity = fields.Float(
        required=False,
        allow_none=True,
        missing=None,
        validate=validate.Range(min=0.01, error="Consumed quantity must be greater than 0"),
        error_messages={'invalid': 'Consumed quantity must be a valid number'}
    )


class MarkFoodConsumedSchema(Schema):
    """Schema para validar marcar comida como consumida"""
    
    consumed_portions = fields.Float(
        required=False,
        allow_none=True,
        missing=None,
        validate=validate.Range(min=0.01, error="Consumed portions must be greater than 0"),
        error_messages={'invalid': 'Consumed portions must be a valid number'}
    )


class ConsumedResponseSchema(Schema):
    """Schema para la respuesta de items consumidos"""
    
    message = fields.Str()
    action = fields.Str()
    consumed_at = fields.Str()
    
    # Campos dinámicos según el tipo
    ingredient = fields.Str(missing=None, allow_none=True)
    food = fields.Str(missing=None, allow_none=True)
    
    consumed_quantity = fields.Float(missing=None, allow_none=True)
    consumed_portions = fields.Float(missing=None, allow_none=True)
    
    remaining_quantity = fields.Float(missing=None, allow_none=True)
    remaining_portions = fields.Float(missing=None, allow_none=True)
    
    unit = fields.Str(missing=None, allow_none=True)
    
    stack_removed = fields.Bool(missing=None, allow_none=True)
    food_removed = fields.Bool(missing=None, allow_none=True)
    
    original_added_at = fields.Str()
    food_details = fields.Dict(missing=None, allow_none=True) 