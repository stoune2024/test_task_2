import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Query, HTTPException, Body
from sqlmodel import SQLModel, create_engine, Session, Field, select, Relationship
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from contextlib import asynccontextmanager

from ..config import settings

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
    competence: str | None = Field(default=None)


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


engine = create_engine(f"postgresql+psycopg2://"
                       f"{settings.postgres_user}:"
                       f"{settings.postgres_password}@"
                       f"{settings.postgres_host}:"
                       f"{settings.postgres_port}/"
                       f"{settings.postgres_db_name}"
                       )


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(router: APIRouter):
    create_db_and_tables()
    yield


router = APIRouter(tags=['Взаимодействие с БД'], lifespan=lifespan)


@router.post(
    "/reg/",
    # response_class=HTMLResponse
)
def create_user(
        user: Annotated[UserCreate, Form()],
        session: SessionDep,
        request: Request
):
    """
Функция создает пользователя и добавляет его в базу данных.
Может использоваться также для обновления данных пользователя.
    """
    try:
        hashed_password = pwd_context.hash(user.password)
        extra_data = {"hashed_password": hashed_password}
        db_user = UserTable.model_validate(user, update=extra_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        # return templates.TemplateResponse(request=request, name="notification.html")
        return {"message": "user is created"}
    except IntegrityError as e:
        return {"message": "Oops, the data you wrote refers to an existing user. Try again",
                "error": f"error {e} has occured"
                }


@router.get("/users/", response_model=list[UserPublic])
def read_users(
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
):
    """
Функция получения списка пользователей. Возвращает список пользователей модели UserPublic.
    """
    users = session.exec(select(UserTable).offset(offset).limit(limit)).all()
    # users = session.query(UserTable).all()
    return users


@router.patch("/users/{user_id}")
def update_user(
        user_id: int,
        user: Annotated[UserUpdate, Form()],
        session: SessionDep,
):
    """
Функция обновления данных конкретного пользователя в БД. Не поддерживается HTML5 формами, поэтому её роль играет
post-эндпоинт. Тем не менее эндпоинт работает исправно.
    """
    user_db = session.get(UserTable, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="Oops.. User not found")
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
        user_id: int,
        session: SessionDep
):
    """
Функция удаления пользователя из БД. Функция работает, но пока не реализована на практике.

    """
    user = session.get(UserTable, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Oops.. User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}
