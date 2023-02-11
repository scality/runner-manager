from marshmallow import Schema, fields


class AwsConfig(Schema):
    project_id = fields.Str(required=True)
    zone = fields.Str(required=True)


class AwsConfigVmType(Schema):
    machine_type = fields.Str(required=True)
    project = fields.Str(required=True)
    family = fields.Str(required=True)
    disk_size_gb = fields.Str(required=True)
