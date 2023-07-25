# Workflows

A high level description of the runner manager workflows.

## Webhook events

Webhook events are sent by GitHub on selected events, such as:

- Push to a repository
- Pull requests is merged
- A workflow is triggered

In the case of the runner manager, we are interested in `workflow_job` events
that are triggered when a job is queued, running or completed.

Here's a description of the workflow that is triggered by a `workflow_job` event:

```mermaid
sequenceDiagram
    actor Developer
    Developer ->> GitHub: Pushes code
    GitHub ->> GitHub: Triggers a GitHub Actions workflow
    GitHub ->> Runner Manager: Sends webhook event for workflow jobs
    alt The job status is queued
        Runner Manager ->> Runner Manager: Checks how many runners are authorized to run simultaneously
        alt The maximum number of runners is not reached
            Runner Manager ->> Backend: Request a new runner
            participant Runner as Self-hosted Runner
            Backend ->> Runner: Creates a new runner
            activate Runner
            Runner ->> GitHub: Connects to GitHub Actions
        else The maximum number of runners is reached
            Runner Manager ->> Runner Manager: Try again later
        end
    else The job status is running
        Runner Manager ->> Backend: Update the runner status and metadata
    else The job status is completed
        Runner Manager ->> Backend: Delete the runner
        Backend ->> Runner: Deletes the runner
        deactivate Runner
    end
```

## Health checks

It will also periodically check the health of the runners and
perform actions based on their status.

```mermaid
sequenceDiagram
    participant Runner Manager
    participant Redis
    participant Queue
    participant Job
    participant GitHub
    participant Backend
    Runner Manager ->> Redis: Request the list of runners groups
    loop for every runner group
        Runner Manager ->>  Queue: Create a job to check the group's health
        Job ->> Redis: Request the list of runners for the group
        loop for every runner
            Job ->> GitHub: Get the runner status
            Job ->> Backend: Get the runner status
            alt The runner's time to start has expired
                Job ->> Queue: Create a job to re-create the runner.
            else The runner's time to live has expired
                Job ->> Queue: Create a job to delete the runner.
            end
            Job ->> Redis: Update the runner and group information.
        end
        Job ->> Queue: Wait for all created jobs to finish
        Job ->> Redis: Update the runner group information
        alt minimum number of runners is not reached
            Runner Manager ->> Queue: Create a job to create a new runner
        end
        end
```
