# Clouds

The runner manager authenticate and configure itself to a single
cloud provider in order to create instances and
attach them to GitHub Actions as self-hosted runners.

The runner manager will make API calls to GitHub and
setup a cloud init inside the instance to install the required dependencies.

## Configuring your selected cloud

In the `settings.yaml` the `cloud_name` configuration
will be used to select the cloud provider in which the
runner manager will use to host self-hosted runners.

Once selected, the configuration will change
for each cloud provider as they essentially do not
work or authenticate themself in the same way.

Follow the doc for each of the supported cloud provider
for more information.

## Supported cloud providers

The currently supported cloud providers are:

- [Openstack](./openstack.md)
- [Google Cloud](./gcloud.md)


## Supporting a new cloud provider

To develop a new cloud provider add a new folder in
`srcs/runners_manager/vm_creation` containing a `CloudManager`
object matching [CloudManager] interface.

[CloudManager]: https://github.com/scality/runner-manager/blob/main/srcs/runners_manager/vm_creation/CloudManager.py
