from githubkit.rest.models import Runner as GithubRunner
from redis_om import JsonModel


class Runner(JsonModel, GithubRunner):
    pass
