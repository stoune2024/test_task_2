import redis
from app.config import settings

redis_client = redis.Redis(
    # Хост для развертывания без контейнеризации
    host=settings.redis_host,
    # Хости для развертывания с контейнеризвцией (Docker)
    # host=settings.docker_redis_host,
    port=settings.redis_port,
    db=1,
    decode_responses=True,
    password=settings.redis_password
)