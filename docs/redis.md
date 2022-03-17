# Redis integration

For local environment easy development, we can start `docker-compose -f ./docker-composee.yml up`
It start a redis database and the runner manager with a config file.

## credentials 
Defined in the settings file, and set the password with the script arg `--redis-password` or in the environment `REDIS_PASSWORD`
```yaml
redis:
  host: redis
  port: 6379
```

## Usage in the code base
The database is set and manage by the object `RedisManager`, and is instanced as global in `srcs/web/init.py`.

On creation each `RunnerManager` load his data from redis.
There Runner list is always up-to-date with the redis data, same for `Runner` data.
Then, when it creates or update a runner, it automatically updates the data in redis.


## Helm template
```yaml
dependencies:
- name: redis
  version: "15.3.2"
  repository: "https://charts.bitnami.com/bitnami"

```