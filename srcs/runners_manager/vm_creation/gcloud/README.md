

# GcloudManager

The runner have the capability to create resources on Google Cloud. Follow the steps below to authenticate
and configure this service

## Credentials

### Developer Setup

#### Installing gcloud cli

If you already have gcloud installed, configured and authenticated on your own computer you can skip this step.

You need to [install the gcloud cli] on your own computer to create application credentials.

Once the cli installed, you can run the following command configure it:
```bash
gcloud init
```
And follow the instructions prompted by the command. Not sure which zone to pick? Use `us-east1-c`.

#### Creating application credentials

Run the following command to create the according application credentials
to authenticate the runner with your own user:
```bash
# $PROJECT_ID is the google cloud project you want to interact with
export PROJECT_ID=my-gcloud-project
gcloud auth application-default login --project=$PROJECT_ID
```
Follow the instructions and authentication workflow provided by the command.

The following file: `~/.config/gcloud/application_default_credentials.json` should have been created
on your computer, and you should be good to go to use the runner with your own user credentials.

### Daemon setup
If you don't want to use your own user credentials to run this service as a proper daemon per example:

You will need to create a proper service account with the according rights to run
this service authenticated with Google Cloud. Follow Google Cloud documentation
to understand how service account works.

Once the service account was created and you have downloaded the proper application credentials file.

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service/account/file.json
```


## Config

### Service
Considering the application credentials has been setup on the service system,
the remaining service configuration you'll need are:
```yaml
cloud_name: 'gcloud'
cloud_config:
  project_id: my-project-id
  zone: us-east1-c
```

### Runner
Here's an example of a pool of runner on gcloud running with ubuntu:
```yaml
runner_pool:
- config:
    machine_type: e2-standard-2
    project: ubuntu-os-cloud
    family: ubuntu-2004-lts
    disk_size_gb: 20
  quantity:
    min: 2
    max: 4
  tags:
  - ubuntu
  - focal
  - small
```

* List of [images] can be found on Google Cloud console
    * Be aware that you need two parameter, the project and the family
* List of [machine types] can be found on Google Cloud documentation
* disk size can be whatever you chose to be usefull (be frugal but generous ;) )

[images]: https://console.cloud.google.com/compute/images?tab=images&project=scality-devl
[machine types]: https://cloud.google.com/compute/docs/general-purpose-machines?hl=en#e2-standard
[install the gcloud cli]: https://cloud.google.com/sdk/docs/install#deb
