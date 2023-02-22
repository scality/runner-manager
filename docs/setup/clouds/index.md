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
`srcs/runners_manager/vm_creation` containing a
`CloudManager` object matching [CloudManager] interface.

### Retrieving VM parameters

To communicate with the application, the user will provide
a lot of information in a `yml` configuration file, such as
`image_id`, `instance_type`, `security_group_ids`, and so on.

During development, a `config_example.yml` file will be created
to test the setup of the new Cloud Provider and to provide
information about the VM.

Next, to send this information to the new Cloud Provider,
the `AwsConfigVmType` class will be created in the `schema.py`
file, and `xxx = fields.Str(required=True)` will require to
be added for each variable.

!!! info
    If it's not a string, replace Str with the type
    of the variable in question.


To retrieve this information, we use
`runner.vm_type.config["xxx"]` in the new Cloud Manager file.

### How to launch the project for testing

First, create a `.env` file and fill in the necessary
environment variables.

Then, create a `config_example.yml` file
(examples are provided in the subsections depending on
the Cloud Provider).

Finally, launch the project with the command
`docker-compose up --build`.

[CloudManager]: https://github.com/scality/runner-manager/blob/main/srcs/runners_manager/vm_creation/CloudManager.py
