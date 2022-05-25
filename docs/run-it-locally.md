# Run it locally

## TLDR;
- Install docker-compose or podman-compose
- Setup Github's and your cloud provider credentials
- Create your `settings.yaml` file
- Run everything :D


A docker-compose file has been created to help you run the required components for the openstack-actions-runner.

To install `docker-compose` run:
```shell
pip install docker-compose
```

## Credentials

Considering you have followed the instruction on the [config](config.md) section. Create a `.env` file, and set the following vars:
```bash
GITHUB_TOKEN=your.github.token
```

## Settings

Create a settings.yaml file like the following:
```
cp config_example.yml test_settings.yml
```

You can keep most of the settings there, but you should change the following:

[Config file setup](docs/config.md)
## Run

Once the configuration has been set you can boot your docker-compose file like the following:
```bash
docker-compose up --build
```


## (Optional) Ngrok setup

As the openstack-actions-runner depends on webhook to work properly.

Ngrok can help you setup a public url to be used with GitHub webhooks.

Create an account on ngrok.com and configure ngrok on your laptop following the doc on the website.

And on the side you can run ngrok to create a public url for you to work with webhooks.

```
ngrok http 8080
```

## Webhook setup

Setup a webhook at the organization level, should be on a link like the following
`https://github.com/organizations/<your org>/settings/hooks`

* Click on Add Webhook
* In payload url, enter your ngrok url, like the following:
`https://ngrok.url/webhook`
* Content type: application/json
* Click on `Let me select individual events.`
* Select: `Workflow jobs` and `Workflow runs`


## Setting up your testing repo

Create a new repository in the organization you have configured the openstack actions runner.

And push the following workflow in the repository:

```yaml
# .github/workflows/test-self-hosted.yaml
---
name: test-self-hosted
on:
  push:
  workflow_dispatch:
jobs:
  greet:
    strategy:
      matrix:
        person:
        - foo
        - bar
    runs-on:
    - self-hosted
    - myspecifictag # here you ensure that your specific runner will be called
    steps:
    - name: sleep
      run: sleep 120
    - name: Send greeting
      run: echo "Hello ${{ matrix.person }}!"
```

Trigger builds and enjoy :beers:
