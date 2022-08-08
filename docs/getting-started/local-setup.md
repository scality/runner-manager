# Local environment

Setting up your local environment

## Install docker

Docker is required to work with the runner manager.

## Install Poetry

The Runner manager uses [Poetry](https://python-poetry.org/), a Python packaging
and dependency management.

Follow [poetry](https://python-poetry.org/docs/#installation) documentation for proper
installation instruction.

## Install pre-commit

Optionally you can install `pre-commit` like this:

```shell
$ pip3 install pre-commit --user
$ pre-commit install
```

It will run on each commit:

- flake8
- python imports reorders
- Somme default pre-commit webhooks to keep your code clean and nice to read.

## Credentials

Some credentials are required to get the runner-manager up and running:

* Admin access to a [GitHub organization](../setup/config.md#github)
* Access to a supported [cloud provider](../setup/clouds/)
