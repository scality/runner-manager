# Config

## Github
### Creating your GitHub Token

* Go into your [tokens settings](https://github.com/settings/tokens)
* Select generate new token
* Name your token
* Apply the following scopes:
  1. `repos`
  2. `workflow`
  3. `admin:org`

## Cloud Manager
Depending on the cloud manager you are using you will need to look at a special documentation.
Here is a list of current backend managed:
- Openstack [link](../srcs/runners_manager/vm_creation/openstack/README.md)


## Settings

When configuring the runner, a `settings.yaml` file needs to be created. The path of this file can be set with the `SETTING_FILE` environment variable.

A [config_example.yml](../config_example.yml) is available with proper description on all the available settings.
