from fastapi import FastAPI, Request

from app.routers.db import router as db_router
from app.routers.safety import router as safety_router

description = """
Данный API был взят из моего PET-проекта. Некоторые модули были удалены с целью соответствия заданию.

## Взаимодействие с БД

Данные эндпоинты полностью соответствуют условию задания. В этом разделе Вы можете с ними поэкспереминитровать.

## Безопасность

Данные эндпоинты не рекомендуются к использованию в Swagger UI, так как они настроены для работы с Cookie-файлами
и сохранением в них JWT токена. В данном API они не работают. Решил их не убирать, потому что в таком случае
пришлось бы изменять Pydantic модели и вносить прочие изменения. Реализация данных эндпоинтом и модуля safety
представлены в моем PET-проекте №2. 
"""


app = FastAPI(
    title="Тестовое задание №2 для ИТК Академии",
    description=description,
    version="0.0.1",
    contact={
        "name": "Чубаров Максим Алексеевич",
        "email": "mchubaroff@yandex.ru",
    },
)


app.include_router(db_router)
app.include_router(safety_router)