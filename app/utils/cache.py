import json
import redis
from app.core.config import settings

REDIS_URL = settings.REDIS_URL if hasattr(
    settings, 'REDIS_URL') else "redis://localhost:6379/0"
CACHE_TTL = 3600

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    CACHE_ENABLED = True
except:
    CACHE_ENABLED = False
    redis_client = None


def get_cached(key):
    if not CACHE_ENABLED:
        return None

    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except:
        return None


def set_cached(key, data, ttl=CACHE_TTL):
    if not CACHE_ENABLED:
        return False

    try:
        redis_client.setex(key, ttl, json.dumps(data))
        return True
    except:
        return False


def delete_cached(key):
    if not CACHE_ENABLED:
        return False

    try:
        redis_client.delete(key)
        return True
    except:
        return False


def clear_cache_pattern(pattern):
    if not CACHE_ENABLED:
        return False

    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
    except:
        return False
