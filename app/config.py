from pydantic_settings import BaseSettings, SettingsConfigDict
import os


# Класс для управления настройками приложения через Pydantic
class Settings(BaseSettings):
    secret_key: str                     # Секретный ключ подписи JWT-токенов
    algorithm: str                      # Алгоритм шифрования подписей JWT-токенов
    access_token_expire_minutes: int    # Время истечения срока годноcти JWT-токена
    postgres_user: str                  # Имя пользователя Postgres
    postgres_password: str              # Пароль пользователя Postgres
    postgres_host: str                  # Адрес хоста Postgres
    postgres_port: int                  # Порт Postgres
    postgres_db_name: str               # Имя базы данных Postgres

    def get_db_url(self):
        return (f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}")

    # Указание файла с переменными окружения
    model_config = SettingsConfigDict(env_file=f"{os.path.dirname(os.path.abspath(__file__))}/../.env")

settings = Settings()