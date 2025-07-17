from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from functools import lru_cache

import jwt
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.templating import Jinja2Templates
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.exc import InvalidRequestError
from sqlmodel import create_engine, Session, select, SQLModel

from .db import UserTable, SessionDep
from ..config import settings, Settings


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """ Расширяет функционал класса OAuth2PasswordBearer с целью получения JWT-токена из Cookie"""

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if authorization is not None:
            scheme, param = get_authorization_scheme_param(authorization)
            if not authorization or scheme.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not find Authorization header",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None
            return param
        token = request.cookies.get('access-token')
        if token:
            param = token
            return param
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not find token",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Контекст PassLib. Используется для хэширования и проверки паролей.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


@lru_cache()
def get_settings():
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """
Функция проверки соответствия полученного пароля и хранимого хеша
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(
        username: str,
        session: SessionDep
):
    """
Функция получения информации о пользователе из БД
    """
    try:
        user = session.exec(select(UserTable).where(UserTable.username == username)).one()
        return user
    except InvalidRequestError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(
        username: str,
        password: str,
        session: SessionDep
):
    """
Функция аутентификации и возврата пользователя
    """
    user = get_user(username, session)
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(
        settings: SettingsDep,
        data: dict,
        expires_delta: timedelta | None = None,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def verify_token(
        settings: SettingsDep,
        token: Annotated[str, Depends(oauth2_scheme)],
        request: Request,
        session: SessionDep
):
    """ Функция проверки JWT-токена пользователя и возврата токена с username пользователя, если все в порядке. """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not find token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(token_data.username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not find user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


router = APIRouter(tags=['Безопасность'])


@router.post("/login")
async def validate_login_form(
        request: Request,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: SessionDep,
        settings: SettingsDep
):
    """
Эндпоинт отвечает за обработку данных, пришедших из формы авторизации. Если пользователь успешно прошел
аутентификацию и авторизацию JWT-токен сохраняется в куках. Происходит перенаправление на другую страницу.

    """
    token = await login_for_access_token(request, form_data, session, settings)
    access_token = token.get("access_token")
    redirect_url = "/suc_auth"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = RedirectResponse(
        redirect_url, status_code=status.HTTP_303_SEE_OTHER, headers=headers
    )
    response.set_cookie(
        key='access-token', value=access_token, httponly=True, secure=True)
    return response


@router.post("/token")
async def login_for_access_token(
        request: Request,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: SessionDep,
        settings: SettingsDep
):
    """
Эндпоинт отвечает за аутентификацию пользователя и генерацию JWT-токена. Функция работает как зависимость
в эндпоинте POST /login

    """
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not find user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        settings,
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
