# Config

When configuring the runner, a `settings.yaml` file needs to be created.
The path of this file can be set with the `SETTING_FILE` environment variable.

A [config_example.yml] is available with proper description on all
the available settings.

## Github

### Pick or create your GitHub organization

The runner manager can only attach itself to a GitHub organization.

Admin access on the organization is required to configure and
use the runner manager. Chose between:

* Setting it up on an existing one that you have the appropriate credentials.
* Request admin access to your appropriate entity.
* [create a new one] (there's a free option).

> It is perfectly possible to attach the runner to a repository instead
of a whole GitHub Organization, making it easier to test and work with.
However this feature was never implemented, contributions are welcome ;)

### Creating your GitHub Token

* Go into your [tokens settings](https://github.com/settings/tokens)
* Select generate new token
* Name your token
* Apply the following scopes:

    * `repos`
    * `workflow`
    * `admin:org`

The token shall be set as the `GITHUB_TOKEN` environment
variable in the container runtime of the runner manager.


## Cloud configuration

`cloud_name` must match the one of the supported cloud provider:

- `gcloud`
- `openstack`

The values for `cloud_config` can be found in the
documentation of your [selected cloud provider]

```yaml
# Your github organization where you want to attach your self-hosted runners
github_organization: ""

# Cloud connection infos
cloud_name: 'cloud_manager_name'
cloud_config:
# Depends on your cloud
...
```

###  Your Runners pool

Runner pools are the group of instances that the runner
manager will manage.

This is how you can define the specifications of each
instances and how they are selected
(thanks to the assigned tags)

Each runner pool will typically have:

* The OS image. (cloud specific)
* The flavor of an instance. (cloud specific)
* The disk size, if different from the flavor. (cloud specific)
* The minimum quantity of runner available. The runner manager
will do it's best to always make the number of instances defined in this
setting available and ready to pick up jobs.
* The maximum quantity of runner available.
This setting ensure that there won't be an infinite
amount of resources created at a given time.
* The tags, this is how users will selected the given
runner pool in their GitHub Actions workflows.

For cloud specific configuration have a look at your [selected cloud provider].

```yaml
runner_pool:
  - config:
    # Depends on your cloud configuration
      ...
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

[config_example.yml]: https://github.com/scality/runner-manager/blob/main/config_example.yml
[create a new one]: https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/creating-a-new-organization-from-scratch
[selected cloud provider]: ./clouds/index.md
