# Run it locally

In this guide you'll do the following:

- Install docker-compose or podman-compose
- Setup Github's and your cloud provider credentials
- Create your `settings.yaml` file
- Run everything :D

Before starting this guide:

* Follow the [local setup](./local-setup.md) documentation.
* Get familiar with the [config](../setup/config.md).
* Made your [cloud](../setup/clouds/index.md) provider choice.

## Credentials

Create a GitHub personal access.
Instructions can be found on the [config](../setup/config.md#github) section.

Create a `.env` file, and set the following vars:

```bash
GITHUB_TOKEN=<insert your github token>
```

## Settings

Create a `settings.yaml` file like the following:
```bash
cp config_example.yml test_settings.yml
```

Most of the settings can be set as is, however, review the specs defined in
the [configuration](../setup/config.md) instructions and change the yaml file
according to your needs.


## Run

Once the configuration has been set you can boot your docker-compose file like the following:

```bash
poetry run docker-compose up --build
```

## Webhook setup

### Ngrok setup

As the runner manager depends on webhook coming from github to work properly.

Ngrok can help you setup a public url to be used with GitHub webhooks.

Create an account on ngrok.com and configure ngrok on your laptop following the doc on the website.

And on the side you can run ngrok to create a public url for you to work with webhooks.

```
ngrok http 8080
```

### Setting up the webhook

Setup a webhook at the organization level, should be on a link like the following
`https://github.com/organizations/<your org>/settings/hooks`

* Click on Add Webhook
* In payload url, enter your ngrok url, like the following:
`https://ngrok.url/webhook`
* Content type: application/json
* Click on `Let me select individual events.`
* Select: `Workflow jobs` and `Workflow runs`


## Setting up your testing repo

Create a new repository in the organization you have configured the runner manager.

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
