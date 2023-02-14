# AWS

The runner have the capability to create resources on AWS. Follow the steps below to authenticate
and configure this service


## Credentials

Set the following environment variables, with your respective AWS credentials:

* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`
* `AWS_SESSION_TOKEN` (Optional)

## Config

### AWS Region

Configure the region where EC2 instances will be created with the `AWS_DEFAULT_REGION` environment variable. Per example `us-west-2`.

### Service

Considering the application credentials has been setup on the service system,
the remaining service configuration you'll need are:

```yaml
cloud_name: 'aws'
cloud_config: {}

### Runner
Here's an example of a pool of runner on aws running with Ubuntu (image_id corresponding to it):
```yaml
runner_pool:
  - config:
      image_id: 'ami-0735c191cf914754d'
      instance_type: 't2.micro'
      security_group_ids:
        - 'sg-XXX'
        - 'sg-XXX'
      subnet_id: 'subnet-XXX'
      disk_size_gb: 30
    quantity:
      min: 2
      max: 4
    tags:
      - aws
      - ubuntu
      - jammy
      - small
```

* As for the information and characteristics to be filled in, you can find them in the [AWS management console].

[AWS management console]: https://us-west-2.console.aws.amazon.com/console/home?region=us-west-2#
