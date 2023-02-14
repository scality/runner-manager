from marshmallow import Schema, fields


class AwsConfig(Schema):
    region = fields.Str(required=False)


class AwsConfigVmType(Schema):
    image_id = fields.Str(required=True)
    instance_type = fields.Str(required=True)
    security_group_ids = fields.List(fields.String())
    subnet_id = fields.Str(required=True)
    disk_size_gb = fields.Int(required=True)
