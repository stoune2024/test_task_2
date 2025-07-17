import redis
from ..config import settings

# Подключение к redis
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

# redis://redis@localhost:6379/0

# Запись словаря по ключу
# redis_client.hset('user-session:123', mapping={
#     'name': 'John',
#     "surname": 'Smith',
#     "company": 'Redis',
#     "age": 36,
# })

# Запись списка по ключу
# redis_client.lpush('my_list', 'orange', 'apple', 'watermelon')

# Чтение словаря по ключу
# data = redis_client.hgetall('user-session:123')

# Чтение списка по ключу
# data_2 = redis_client.lrange('my_list', 0, -1)

# Запись списка по ключу. Альтернативный вариант
# redis_client.lpush('index_page_nav', ", ".join(index_page_nav))



# for i in index_page_nav:
#     redis_client.lpush('index_page_nav', i)
#
# for i in index_page_about:
#     redis_client.lpush('index_page_about', i)
#
# for i in barsik_page_nav:
#     redis_client.lpush('barsik_page_nav', i)
#
# for i in barsik_page_about:
#     redis_client.lpush('barsik_page_about', i)
#
# for i in marsik_page_nav:
#     redis_client.lpush('marsik_page_nav', i)
#
# for i in marsik_page_about:
#     redis_client.lpush('marsik_page_about', i)
#
# for i in bonus_page_nav:
#     redis_client.lpush('bonus_page_nav', i)
#
# for i in bonus_page_about:
#     redis_client.lpush('bonus_page_about', i)

# res = redis_client.get('settings_changed')
# redis_client.rpush('marsik_page_nav_verif', 'О Барсике', 'На главную', 'Кусь Барсика', 'Настройки', 'Log Out')
# print(res)