import redis.asyncio as redis
from app.config import settings

pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis():
    return redis.Redis(connection_pool=pool)
