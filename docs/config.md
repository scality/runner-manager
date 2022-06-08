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
- Google Cloud [link](../srcs/runners_manager/vm_creation/gcloud/README.md)


## Settings

When configuring the runner, a `settings.yaml` file needs to be created. The path of this file can be set with the `SETTING_FILE` environment variable.

A [config_example.yml](../config_example.yml) is available with proper description on all the available settings.

Depending on your need you should set this config:

### GitHub and Cloud provider
`cloud_name` must match the folder name in `./srcs/runners_manager/vm_creation` containing a `CloudManager` object matching
[CloudManager](../srcs/runners_manager/vm_creation/CloudManager.py) interface.
```yaml
# Your github organization where you want to attach your self-hosted runners
github_organization: ""

# Cloud connection infos
cloud_name: 'cloud_manager_name'
cloud_config:
  "See your cloud config docs"
```

###  Your Runners pool
```yaml
runner_pool:
  - config:
      - "Look at your Cloud Manager conig"
    quantity:
      min: 2
      max: 10
    tags:
      - bionic
      - small
# To ease up testing on this specific pool of runner
# Add a very unique tag so that you can select, precisely, your runner
      - myspecifictag
```
