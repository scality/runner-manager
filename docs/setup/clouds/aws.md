# AWS

The runner have the capability to create resources on AWS. Follow the steps below to authenticate
and configure this service

## Credentials

### Get credentials for Engineering-EC2User

Go on AWS Single Sign-on to get the credentials.
Then click on the link called "Command Line or programmatic access".
Get :
- AWS Access Key Id
- AWS Secret Access Key
- AWS Session Token

Create a .env file at the root of the project and put in it :
AWS_ACCESS_KEY_ID="XXX"
AWS_SECRET_ACCESS_KEY="XXX"
AWS_SESSION_TOKEN="XXX"

You will also have to fill in AWS_DEFAULT_REGION (us-west-2 for example) and GITHUB_TOKEN (your github token).

## Config

### Service

Considering the application credentials has been setup on the service system,
the remaining service configuration you'll need are:
```yaml
cloud_name: 'aws'
cloud_config: {}
```

### Runner
Here's an example of a pool of runner on aws running with ubuntu:
```yaml
runner_pool:
  - config:
      image_id: 'ami-XXX'
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
