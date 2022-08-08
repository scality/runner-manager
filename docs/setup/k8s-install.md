# Chart install for Runner manager

A chart has been developed to install the runner-manager on k8s.

## Install

```bash
helm install my-runner-manager charts/runner-manager
```

## Config

The configuration is similar to what is defined on the `settings.yaml` file.

Checkout the [values.yaml] to know about all the settings available.

### Mandatory values

```yaml
githubToken: ""
githubOrganization: ""

# Cloud connection name
cloudName: 'openstack'
# Cloud config, it will change depending on your cloud
cloudConfig: {}

# SSh keys allowed to connect on created VM, username is `actions`
allowedSshKeys: ''

# Represent the infos about each group of runners
# Define by:
#  - There config depending on the cloud backend
#  - The quantity allowed to spawn at the same time
#  - The tags use by github actions
# Example:
# runner_pool:
#   - config:
#       flavor: 'm1.small'
#       image: 'CentOS 7 (PVHVM)'
#     quantity:
#       min: 2
#       max: 4
#     tags:
#       - centos7
#       - small
runnerPool: []
```

## Overridable values
```yaml
# The python module, used for configuration
pythonConfigModule: 'settings.settings_local'

# If a runner is not used for the extraRunnerTime, and there is enough runners, he is deleted
extraRunnerTimer:
  minutes: 10
  hours: 0

# If the runner is not spawned after this timer, it is considered as dead, and is deleted.
timeoutRunnerTimer:
  minutes: 15
  hours: 0
```

[values.yaml]: https://github.com/scality/runner-manager/blob/main/charts/runner-manager/values.yaml
