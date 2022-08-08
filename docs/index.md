# Runner Manager

The runner manager is a software used to create predefined Virtual machines
on different cloud providers in order to manage
GitHub Action self-hosted runners.

Each instance will connect itself to github.com and run GitHub Actions jobs.
When a job ends, the runner manager will take care of recycling the machine
with a new one to handle the next jobs to come.
