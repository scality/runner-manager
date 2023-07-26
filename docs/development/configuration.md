# Configuration

The runner manager can be configured as a GitHub Application
(recommended for production)
but also with a GitHub Personal Access Token (recommended for development).

The configuration of the runner will be done through a YAML file and
a combination of environment variables for secrets.

## Global configuration

The global configuration will contain the following information:

- A name for the runner manager. (default: runner-manager)
  It will be used as a metadata or prefix which will allow the runner to identify
  the owner of each resources, avoiding conflicts with other runner managers or users.
- The GitHub Authentication parameters. (Required)
  - For GitHub Application: The GitHub Application ID, Installation ID and Private Key. (Required)
  - For GitHub Personal Access Token: The GitHub Personal Access Token. (Required)
- The Redis connection parameters. (Required)
- The backends configuration. (Required)
- The webhook secret. (Required)
- The runner groups. (Required)
- The health check interval. (Default: 10 minutes)
- The runner's time to start. (Default: 10 minutes)
- The runner's time to live. (Default: 12 hours)

## Runner groups

A list of runner groups will be configured into the runner manager
settings file.
The following information will be configured for each runner group:

- Name of the group. (Required)
- Name of the GitHub Organization in which the runner and group will be created. (Required)
- Name of the GitHub Repository in which the runner and group will be created. (Optional)
- Repository access:
  - A list of selected repositories. (Default: All repositories)
  - Allow public repositories. (Default: True)
- Workflow access: a comma separated list of the workflows that can access the runner group.
  For example:
  ```shell
  octo-org/octo-repo/.github/workflows/build.yml@v2,
  octo-org/octo-repo/.github/workflows/deploy.yml@d6dc6c96df4f32fa27b039f2084f576ed2c5c2a5,
  monalisa/octo-test/.github/workflows/test.yml@main
  ```
- The name of the workflow that will be used to run the jobs. (Optional)
- The maximum number of runners that can run simultaneously. (Default: 20)
- The minimum number of runners that must be available. (Default: 0)
- The runner labels that will be attached to the runners of the group. (Required)
- The runner backend that will be used to host the runners of the group. (Required)
- The runner's instance specifications (CPU, RAM, disk, etc). (Required)
