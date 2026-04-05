import json
import os

import redis
from redis.exceptions import RedisError


REDIRECT_CACHE_PREFIX = "redirect:"
REDIRECT_CACHE_TTL_SECONDS = int(
    os.getenv("REDIRECT_CACHE_TTL_SECONDS", "300"))
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None

    _redis_client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    return _redis_client


def _redirect_cache_key(short_code: str) -> str:
    return f"{REDIRECT_CACHE_PREFIX}{short_code}"


def set_redirect_cache(url) -> None:
    client = _get_redis_client()
    if not client:
        return

    payload = {
        "url_id": url.id,
        "original_url": url.original_url,
        "is_active": bool(url.is_active),
    }
    try:
        client.setex(
            _redirect_cache_key(url.short_code),
            REDIRECT_CACHE_TTL_SECONDS,
            json.dumps(payload),
        )
    except RedisError:
        return


def get_redirect_cache(short_code: str):
    client = _get_redis_client()
    if not client:
        return None

    try:
        cached = client.get(_redirect_cache_key(short_code))
    except RedisError:
        return None

    if not cached:
        return None

    try:
        payload = json.loads(cached)
    except (TypeError, json.JSONDecodeError):
        return None

    if "original_url" not in payload or "is_active" not in payload:
        return None
    return payload


def delete_redirect_cache(short_code: str) -> None:
    client = _get_redis_client()
    if not client:
        return

    try:
        client.delete(_redirect_cache_key(short_code))
    except RedisError:
        return
