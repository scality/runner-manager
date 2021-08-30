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
On creation each `RunnerManager` load his data from redis. 
Then, when it creates or update a runner, it automatically updates the data in redis.


## Helm template
```yaml
dependencies:
- name: redis
  version: "15.3.2"
  repository: "https://charts.bitnami.com/bitnami"

```