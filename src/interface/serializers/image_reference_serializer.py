from marshmallow import Schema, fields

class ImageReferencePublicSchema(Schema):
    name = fields.Str(required=True)
    image_path = fields.Str(required=True)
    image_type = fields.Str(required=True)
