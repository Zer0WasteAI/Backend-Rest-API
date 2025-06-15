from marshmallow import Schema, fields, validate


class UploadImageRequestSchema(Schema):
    item_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=100, error="item_name must be between 2 and 100 characters"),
            validate.Regexp(r'^[a-zA-Z0-9\s\-_.]+$', error="item_name contains invalid characters")
        ],
        error_messages={'required': 'item_name is required'}
    )
    
    image_type = fields.Str(
        required=False,
        missing='default',
        validate=validate.OneOf(['food', 'ingredient', 'default']),
        error_messages={'invalid': 'image_type must be one of: food, ingredient, default'}
    )


class UploadImageResponseSchema(Schema):
    message = fields.Str()
    image = fields.Dict(keys=fields.Str(), values=fields.Raw()) 