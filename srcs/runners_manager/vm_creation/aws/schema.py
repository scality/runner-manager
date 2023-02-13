from marshmallow import Schema, fields


class AwsConfig(Schema):
    region = fields.Str(required=True)


class AwsConfigVmType(Schema):
    image_id = fields.Str(required=True)
    instance_type = fields.Str(required=True)
    security_group_ids = fields.Str(required=True)
    subnet_id = fields.Str(required=True)
    disk_size_gb = fields.Str(required=True)
