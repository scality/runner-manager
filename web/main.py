import os
import redis
from fastapi import FastAPI

app = FastAPI()
redis_database = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'),
                             port=os.getenv('REDIS_PORT', '6379'),
                             password=os.getenv('REDIS_PASSWORD', None))
redis_database.keys()


@app.get("/")
async def root():
    keys = {}
    for elem in redis_database.keys():
        keys[elem] = redis_database.get(elem)

    return {"message": "Hello World", "redis_database": keys}
