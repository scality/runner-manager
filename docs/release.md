# Release

To release the runner-manager a [GitHub Workflow] has been
created to take care of all the tasks required.

## GitHub Workflow

The [release workflow] will take as input:

* The branch that needs to be tagged
* The name of the tag desired.

During execution the following will be produced:

* A docker image will be built and pushed
* A tag will be made in the repository
* A [GitHub Release] will be made.

## Making a release

Use the workflow dispatch function for the [release workflow]
and create a new run.

!!! tip

    You can also use the GitHub CLI like the following:
    ```shell
    gh workflow run release.yml -f tag=<tag name>
    ```

## Releases

All releases available will be displayed on the [GitHub Release]
page of the repository.

[GitHub Workflow]: https://github.com/scality/runner-manager/blob/main/.github/workflows/release.yml
[GitHub Release]: https://github.com/scality/runner-manager/releases
[release workflow]: https://github.com/scality/runner-manager/actions/workflows/release.yml
