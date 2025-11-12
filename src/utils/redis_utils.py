import redis

def clear_redis(redis_url: str = 'redis://localhost:6379/0', key_prefix: str = 'scrapy:dupefilter'):
    redis_client = redis.from_url(redis_url, decode_responses=True)
    pattern = f"{key_prefix}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
    redis_client.close()