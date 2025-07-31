import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Query, HTTPException, Body, Path
from sqlmodel import SQLModel, create_engine, Session, Field, select, Relationship
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr
from psycopg2.errors import DuplicateDatabase
from passlib.context import CryptContext
from contextlib import asynccontextmanager
import jwt


from ..config import settings
from .db_connection import create_database

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserBase(SQLModel):
    """ Модель, дополняющая сведения о работниках """
    email: EmailStr | None = Field(default=None, unique=True)
    phone_number: str | None = Field(default=None, unique=True)
    dep: str | None = Field(default=None)
    sub_dep: str | None = Field(default=None)
    first_name: str | None = Field(default=None)
    second_name: str | None = Field(default=None)
    third_name: str | None = Field(default=None)
    position: str | None = Field(default=None)
    tab_no: int | None = Field(default=None, unique=True)
    registered_on: datetime.date | None = Field(default=None)
    is_admin: bool = Field(default=False)


class UserTable(UserBase, table=True):
    """ Таблица с основной информацией о сотрудниках """
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hashed_password: str
    nvo_docs: list["NvoTable"] = Relationship(back_populates="usertable")


class UserPublic(UserBase):
    id: int


class UserCreate(UserBase):
    username: str
    password: str


class UserUpdate(UserBase):
    username: str | None = None
    password: str | None = None


class NvoTable(SQLModel, table=True):
    """ Таблица с данными о заявлениях на НВО от работников """
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key='usertable.id')
    shift_worked: datetime.date
    day_off: datetime.date
    usertable: UserTable | None = Relationship(back_populates='nvo_docs')
    submission_day: datetime.date


def get_metadata():
    return SQLModel.metadata


database_url = settings.get_db_url()


engine = create_engine(database_url)


def create_db_and_tables():
    try:
        create_database()
        SQLModel.metadata.create_all(engine)
    except DuplicateDatabase:
        print('Attempt to create existing database. Nothing to worry about)')


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(router: APIRouter):
    create_db_and_tables()
    yield


router = APIRouter(
    tags=['Взаимодействие с БД'],
    lifespan=lifespan
)


@router.post(
    "/reg/",
)
def create_user(
        user: Annotated[UserCreate, Form()],
        session: SessionDep,
):
    """
    Эндпоинт создания (регистрации нового пользователя)
    :param user: Данные о пользователе, приходящие из HTML формы. Валидируются Pydantic моделью UserCreate
    :param session: Объект типа Session (сессия) для взаимодействия с БД
    :return: JSON-строка, сообщающая о результате выполнения эндпоинта
    """
    try:
        hashed_password = pwd_context.hash(user.password)
        extra_data = {"hashed_password": hashed_password}
        db_user = UserTable.model_validate(user, update=extra_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return {"message": "user is created"}
    except IntegrityError as e:
        return {"message": "Oops, the data you wrote refers to an existing user. Try again",
                "error": f"error {e} has occured"
                }


@router.get("/users/", response_model=list[UserPublic])
def read_users(
        session: SessionDep,
        offset: Annotated[
            int,
            Query(
                title='Отступ для списка пользователей',
                ge=0,
                le=1000,
            )
        ] = 0,
        limit: Annotated[
            int,
            Query(
                title='Ограначитель списка пользователей',
                ge=0,
                le=1000
            )
        ] = 10,
):
    """
    Эндпоинт получения списка пользователей.
    :param session: Объект типа Session (сессия) для взаимодействия с БД
    :param offset: Отступ для списка пользователей (условно их максимум 1000). Используется для пагинации
    :param limit: Ограничитель максимального количества отображаемых пользователей. Используется для пагинации.
    :return: Список пользователей, валидированных моделью UserPublic
    """
    users = session.exec(select(UserTable).offset(offset).limit(limit)).all()
    return users


@router.get("/users/{user_id}", response_model=UserPublic)
def update_user(
        session: SessionDep,
        user_id: Annotated[
            int,
            Path(
                title='Идентификатор пользователя',
                ge=0,
                le=1000
            )
        ],
):
    """
    Эндпоинт получения конкретного пользователя по идентификатору из БД.
    :param session: Объект типа Session (сессия) для взаимодействия с БД
    :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
    :return: Объект пользователь, валидируемый моделью UserPublic
    """
    user_db = session.get(UserTable, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user_db



@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(
        user_id: Annotated[
            int,
            Path(
                title='Идентификатор пользователя',
                ge=0,
                le=1000
            )
        ],
        user: Annotated[UserUpdate, Form()],
        session: SessionDep,
):
    """
    Эндпоинт обновления данных о пользователе.
    :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
    :param user: Данные о пользователе, приходящие из HTML формы. Валидируются Pydantic моделью UserUpdate
    :param session: Объект типа Session (сессия) для взаимодействия с БД
    :return: Объект пользователь, валидируемый моделью UserPublic
    """
    user_db = session.get(UserTable, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user_data = user.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = pwd_context.hash(password)
        extra_data["hashed_password"] = hashed_password
    user_db.sqlmodel_update(user_data, update=extra_data)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db


@router.delete("/users/{user_id}")
def delete_user(
        user_id: Annotated[
            int,
            Path(
                title='Идентификатор пользователя',
                ge=0,
                le=1000
            )
        ],
        session: SessionDep
):
    """
    Эндпоинт удаления данных о конкретном пользователе
    :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
    :param session: Объект типа Session (сессия) для взаимодействия с БД
    :return: JSON-строка, сообщающая о результате выполнения эндпоинта
    """
    user = session.get(UserTable, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    session.delete(user)
    session.commit()
    return {"ok": True}
