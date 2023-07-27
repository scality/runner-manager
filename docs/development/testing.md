# Testing

Tests will be written using [pytest](https://docs.pytest.org/en/stable/).

The following type of tests wil be written:

- Unit tests.
- API tests.
- Functional tests.

Python dependencies for testing will be configured in the `dev` poetry group:

```shell
# Install all dependencies.
poetry install
# Install only dev dependencies.
poetry install --only dev
# Add new dev dependency.
poetry add --group dev <dependency>
# Update dev dependencies.
poetry update --only dev
```

Each type of test shall generate a coverage report that will be
later used with services like [codecov](https://codecov.io/) to
ensure that the code is properly tested.

## Mocking servers

For the ease of setup and local development, mocking servers will be used
mostly to test interactions with external services.

### GitHub's API

To mock GitHub's API we will use the openapi specification of the API
to generate a mock server that will be used in the unit tests.

The mock server will be generated using [prism](https://github.com/stoplightio/prism)
and will be run in a docker container.

Here's an example of a curl command that will create a new repository to a prism mock server:

```shell
curl -L \
  -X POST \
  -H "Content-Type: application/json" \
  "http://localhost:4010/orgs/scality/repos" \
  -d '{
    "name":"hello-world",
    "description":"This your first repo!",
    "homepage":"https://github.com",
    "private":false,
    "has_issues":true,
    "has_projects":true,
    "has_wiki":true
}'
```

## Unit tests

Unit tests of methods and functions.

The test environment will be configured with:

- Ideally a fakeredis backend, but a real redis server can be used.
- A mock backend, no real runners will be created.
- A mocked queue, no real rq are required.

## API tests

Will make use of the [fastapi test client](https://fastapi.tiangolo.com/advanced/testing/)
to test the runner-manager behavior from the API point of view.

The test environment will be configured with:

- A real redis server.
- A real rq worker to process the jobs.
- A mock backend, no real runners will be created.
- [GitHub's API mock](#githubs-api).

## Functional tests

The functional tests of the runner-manager will be done with no mocking, it will:

- Interact with the real GitHub API.
- Execute a real workflow using [GitHub Actions] triggered by a workflow dispatch.
- Receive webhooks notification from GitHub, thanks to the integration of webhook redirection in `gh` cli.
- Have `docker` configured as a backend to host the runners.

The test environment will be configured with:

- A real redis server.
- A real rq worker to process the jobs.
- The runner manager running as a server but it must still produce a coverage report:

```python
# Here's a code example of how one might do it.
# This code remains to be tested.
import coverage
import os

from fastapi import FastAPI

app = FastAPI()
cov = coverage.Coverage()

@app.on_event("startup")
def startup_event():
    if os.environ.get("CI"):
        cov.start()

@app.on_event("shutdown")
def shutdown_event():
    if os.environ.get("CI"):
        cov.stop()
        cov.save()
```

Pytest parameters will be made available to run the functional tests with different configurations:

- `--backend`: The backend that will be used to host the runners. (Default: docker)
- `--config`: The path to the configuration file. (Default: .config.yaml)

The goal of having those parameters is to allow to run the functional tests
with different configurations, for example:

- `--backend=gcloud --config=.config.yaml`: Run the functional tests with `gcloud` as a backend.
- `--backend=aws --config=.config.yaml`: Run the functional tests with `aws` as a backend.

It is meant to be used by developers to help with the development of backend integrations.
