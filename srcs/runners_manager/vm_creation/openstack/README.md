# Openstack as Cloud Manager
With this object you can spawn each virtual machines in your openstack region, in a defined project, with a network.

## Creating your OpenStack credentials

You can follow OpenStack [API documentation] on how to interact with OpenStack's API.

We require the following settings:
* The OpenStack username to be set as `CLOUD_NINE_USERNAME` as an environment variable
* The Openstack password or the OpenStack token to be set accordingly
  as `CLOUD_NINE_PASSWORD` or `CLOUD_NINE_TOKEN` as environment variables
* The project name / tenant name, to be set as `cloud_nine_tenant` on the `settings.yaml`
* The region in which you will be creating the resources, to be set as `cloud_nine_region`


[API documentation]: https://docs.openstack.org/api-quick-start/api-quick-start.html

## config
`auth_url`, `region_name`, `project_name`, `username`, `password` and `token` are used by `nova_client` python library to authenticate and interact with openstack backend.
`network_name` defined on each subnetwork you virtual machine have access.
All names are defined by nova_client.
```yaml
cloud_config:
  auth_url: ""
  region_name: ""
  project_name: ""

  username: ""
  token | password: ""

  network_name: ""
```
