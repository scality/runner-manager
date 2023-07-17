from fastapi import FastAPI

from runner_manager.models.runner import Runner

app = FastAPI()


@app.put("/runner")
def create_runner(runner: Runner) -> Runner:
    return runner.save()
