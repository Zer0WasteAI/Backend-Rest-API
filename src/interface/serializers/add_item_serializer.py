from marshmallow import Schema, fields, validate, ValidationError


class AddItemToInventorySchema(Schema):
    """Schema para validar datos de agregar item al inventario"""
    
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters"),
            validate.Regexp(r'^[a-zA-Z0-9\s\-_.áéíóúñüÁÉÍÓÚÑÜ]+$', error="Name contains invalid characters")
        ],
        error_messages={'required': 'Name is required'}
    )
    
    quantity = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Quantity must be greater than 0"),
        error_messages={'required': 'Quantity is required'}
    )
    
    unit = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=20, error="Unit must be between 1 and 20 characters"),
            validate.OneOf([
                'gramos', 'gr', 'g',
                'kilogramos', 'kg', 'kilo', 'kilos',
                'litros', 'l', 'lt',
                'mililitros', 'ml',
                'unidades', 'unidad', 'u', 'piezas', 'pieza',
                'tazas', 'taza',
                'cucharadas', 'cda',
                'cucharaditas', 'cdita',
                'porciones', 'porcion',
                'latas', 'lata',
                'paquetes', 'paquete',
                'bolsas', 'bolsa'
            ], error="Invalid unit")
        ],
        error_messages={'required': 'Unit is required'}
    )
    
    storage_type = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50, error="Storage type must be between 1 and 50 characters"),
            validate.OneOf([
                'refrigerador', 'nevera', 'frigorifico',
                'congelador', 'freezer',
                'despensa', 'alacena', 'gabinete',
                'temperatura ambiente', 'ambiente',
                'lugar fresco', 'fresco',
                'lugar seco', 'seco'
            ], error="Invalid storage type")
        ],
        error_messages={'required': 'Storage type is required'}
    )
    
    category = fields.Str(
        required=True,
        validate=validate.OneOf(['ingredient', 'food'], error="Category must be 'ingredient' or 'food'"),
        error_messages={'required': 'Category is required'}
    )
    
    image_url = fields.Url(
        required=False,
        allow_none=True,
        missing=None,
        error_messages={'invalid': 'Invalid URL format'}
    )


class AddItemResponseSchema(Schema):
    """Schema para la respuesta del endpoint add item"""
    
    message = fields.Str()
    item_type = fields.Str()
    item_data = fields.Dict() 