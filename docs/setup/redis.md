# Redis integration

A redis instance is required for the runner manager.

## Usage in the code base

The database is set and managed by the object `RedisManager`,
and is instanced as global in `srcs/web/init.py`.

On creation each `RunnerManager` load his data from redis.
There Runner list is always up-to-date with the redis data,
same for `Runner` data.

Then, when it creates or update a runner,
it automatically updates the data in redis.

## Configuring

Define the host in the settings file, and set the password with the
flag `--redis-password` or in the environment variable `REDIS_PASSWORD`

```yaml
redis:
  host: redis
  port: 6379
```


## Local development setup

To develop on the runner manager with a local instance
of redis, start `docker-compose` file like the following:

```shell
docker-compose -f ./docker-composee.yml up
```

It will start a redis instance and the runner manager configured to it.

## Helm

When installing the runner manager via the helm chart, an installation
of redis is used by default using the bitnami redis chart install.

You may chose to keep it as is or use your own redis installation.
