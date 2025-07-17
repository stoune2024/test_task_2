from pydantic_settings import BaseSettings, SettingsConfigDict
import os


# Класс для управления настройками приложения через Pydantic
class Settings(BaseSettings):
    secret_key: str                     # Секретный ключ подписи JWT-токенов
    algorithm: str                      # Алгоритм шифрования подписей JWT-токенов
    access_token_expire_minutes: int    # Время истечения срока годноcти JWT-токена
    redis_host: str                     # Хост Redis-сервера
    redis_port: int                     # Порт для подключения к Redis
    redis_password: str                 # Пароль для подключения к Redis
    base_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Абсолютная корневая директория проекта
    docker_redis_host: str              # Имя контейнера с Redis
    postgres_user: str                  # Имя пользователя Postgres
    postgres_password: str              # Пароль пользователя Postgres
    postgres_host: str                  # Адрес хоста Postgres
    postgres_port: int                  # Порт Postgres
    postgres_db_name: str               # Имя базы данных Postgres
    smtp_login: str                     # Электронная почта отправителя (системы СПЭД)
    smtp_password: str                  # Пароль для входа в электронную почту
    smtp_password_for_app: str          # Пароль для приложения со стороны почтового сервера
    smtp_host: str                      # Хост smtp протокола

    # Указание файла с переменными окружения
    model_config = SettingsConfigDict(env_file=f"{os.path.dirname(os.path.abspath(__file__))}/../.env")

settings = Settings()