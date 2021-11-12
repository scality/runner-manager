# Config

## Credentials

We require two main kind of credentials:
* A GitHub token to communicate with GitHub's API.
* The Openstack credentials


### Creating your GitHub Token

* Go into your [tokens settings](https://github.com/settings/tokens)
* Select generate new token
* Name your token
* Apply the following scopes:
  1. `repos`
  1. `workflow`
  1. `admin:org`

### Creating your OpenStack credentials

You can follow OpenStack [API documentation] on how to interact with OpenStack's API.

We require the following settings:
* The OpenStack username to be set as `CLOUD_NINE_USERNAME` as an environment variable
* The Openstack password or the OpenStack token to be set accordingly
as `CLOUD_NINE_PASSWORD` or `CLOUD_NINE_TOKEN` as environment variables
* The project name / tenant name, to be set as `cloud_nine_tenant` on the `settings.yaml`
* The region in which you will be creating the resources, to be set as `cloud_nine_region`


[API documentation]: https://docs.openstack.org/api-quick-start/api-quick-start.html


## Settings

When configuring the runner, a `settings.yaml` file needs to be created. The path of this file can be set with the `SETTING_FILE` environment variable.

A [config_example.yml](../config_example.yml) is available with proper description on all the available settings.

