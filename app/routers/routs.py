from fastapi import APIRouter, Request, status, Depends, Form, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from typing import Annotated, Any
from sqlmodel import SQLModel, Field
from sqlalchemy.exc import DataError
import smtplib
from jinja2 import Environment, FileSystemLoader, Template
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import pdfkit
from functools import lru_cache
import os.path
from jwt.exceptions import ExpiredSignatureError, DecodeError

from .safety import TokenData, verify_token, jwt, oauth2_scheme
from .db import SessionDep, NvoTable, UserTable
from .no_sql_db import redis_client
from ..config import settings, Settings

router = APIRouter(tags=['Ручки'])

templates = Jinja2Templates(directory=['templates', 'app/templates', '../app/templates'])
# ISO8859-1
env = Environment(loader=FileSystemLoader('app/templates', encoding='utf-8'))


@lru_cache()
def get_settings():
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


def send_email(
        subject: str,
        from_who: str,
        to_who: str,
        body_content: str,
        filename: str,
        nvo_blank: NvoTable,
        parsed_filename: str,
        settings: SettingsDep,
):
    # Create a text/plain message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_who
    msg['To'] = to_who
    # The main body is just another attachment
    msg.attach(MIMEText(body_content, 'plain'))
    # PDF render
    template = env.get_template(filename)
    output_from_parsed_template = template.render(
        position=f'{nvo_blank.usertable.position}',
        tab_no=f'{nvo_blank.usertable.tab_no}',
        first_name=f'{nvo_blank.usertable.first_name}',
        second_name=f'{nvo_blank.usertable.second_name}',
        third_name=f'{nvo_blank.usertable.third_name}',
        shift_worked=f'{nvo_blank.shift_worked}',
        day_off=f'{nvo_blank.day_off}',
        today_date=date.today(),
        dep=f'{nvo_blank.usertable.dep}',
        sub_dep=f'{nvo_blank.usertable.sub_dep}'
    )
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    pdfkit.from_string(output_from_parsed_template, parsed_filename, configuration=config)
    # PDF attachment
    with open(parsed_filename, 'rb') as attachment:
        part = MIMEBase('application', 'octeat-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    name_of_the_pdf_attachment = os.path.basename(parsed_filename)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename={name_of_the_pdf_attachment}'
    )
    msg.attach(part)
    text = msg.as_string()
    # send via Yandex server
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(settings.smtp_host, 465, context=context) as server:
        server.login(from_who, settings.smtp_password_for_app)
        server.sendmail(from_who, [to_who], text)


class BlankData(SQLModel):
    blank_name: str | None = Field(default=None)


@router.get('/')
async def get_index(
        request: Request,
        session: SessionDep
):
    """ Эндпоинт отображения главного раздела сайта """
    try:
        user_token = request.cookies.get('access-token')
        payload = jwt.decode(user_token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        current_user = session.query(UserTable).filter(UserTable.username == username).one()
        return templates.TemplateResponse(request=request, name='index.html', context={
            'first_name': current_user.first_name,
            'third_name': current_user.third_name,
            'title': redis_client.hget('index_page', 'title')
        })
    except ExpiredSignatureError:
        return RedirectResponse('/auth', status_code=status.HTTP_303_SEE_OTHER)
    except DecodeError:
        return RedirectResponse('/auth', status_code=status.HTTP_303_SEE_OTHER)


@router.get('/auth')
async def get_auth_page(
        request: Request,
):
    """ Эндпоинт отображения страницы с авторизацией """
    return templates.TemplateResponse(request=request, name='index_1.html', context={
        'title': redis_client.hget('oauth_page', 'title')
    })


@router.get('/suc_auth')
async def get_suc_auth_page(
        request: Request,
):
    """ Эндпоинт отображения страницы с авторизацией """
    return templates.TemplateResponse(request=request, name='index_1.html', context={
        'title': redis_client.hget('suc_oauth_page', 'title'),
        'message': redis_client.hget('suc_oauth_page', 'message'),
    })



@router.get('/exit')
async def get_exit_page(
        request: Request,
):
    """ Эндпоинт выхода из учетной записи """
    response = templates.TemplateResponse(request=request, name='index_1.html', context={
        'title': redis_client.hget('log_out_page', 'title'),
        'message': redis_client.hget('log_out_page', 'message')
    })
    response.delete_cookie(key='access-token')
    return response


@router.post('/submit/docs')
async def get_submit_docs_page(
        request: Request,
        data: Annotated[BlankData, Form()],
        session: SessionDep
):
    """ Эндпоинт получения страницы с полями для заполнения """
    try:
        match data.blank_name:
            case "free_day_blank":
                user_token = request.cookies.get('access-token')
                payload = jwt.decode(user_token, settings.secret_key, algorithms=[settings.algorithm])
                username: str = payload.get("sub")
                current_user_id = session.query(UserTable.id).filter(UserTable.username == username).one()
                users_nvo_docs = session.query(NvoTable).filter(NvoTable.user_id == current_user_id.id).all()
                return templates.TemplateResponse(request=request, name='index.html', context={
                    'users_nvo_docs': users_nvo_docs,
                    'title': redis_client.hget('submit_nvo_page', 'title')
                })
            case "fireness_blank":
                return {"message": "заявление об увольнении"}
            case "payement_blank":
                return {"message": "заявление о выплате"}
            case "vacation_blank":
                return {"message": "заявление на отпуск"}
    except ExpiredSignatureError:
        return RedirectResponse('/auth', status_code=status.HTTP_303_SEE_OTHER)
    except DecodeError:
        return RedirectResponse('/auth', status_code=status.HTTP_303_SEE_OTHER)


@router.post('/submit/docs/nvo')
async def submit_nvo_blank(
        raw_token: Annotated[str, Depends(oauth2_scheme)],
        user_token: Annotated[TokenData, Depends(verify_token)],
        session: SessionDep,
        nvo_blank: Annotated[NvoTable, Form()],
        request: Request,
        background_tasks: BackgroundTasks,
        settings: SettingsDep
):
    """ Эндпоинт добавления информации о заявлениях на НВО от работников """
    try:
        payload = jwt.decode(raw_token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if user_token:
            current_user = session.query(UserTable).filter(UserTable.username == username).one()
            nvo_blank_related = NvoTable(
                usertable=current_user,
                shift_worked=nvo_blank.shift_worked,
                day_off=nvo_blank.day_off,
                submission_day=date.today(),
            )
            session.add(nvo_blank_related)
            session.commit()
            session.refresh(nvo_blank_related)
            background_tasks.add_task(send_email(
                'Заявление на НВО от работника',
                settings.smtp_login,
                'mchubaroff@yandex.ru',
                """
                Добрый день, уважаемый пользователь!
                Вам пришло заявление от работника на отгул (см. прикрепленный файл).
                Обратите внимание, что название файла соответсвует табельному номеру сотрудника.
                Источник аутентифицирован и авторизован согласно протоколоу Oauth 2.0 и является достоверным. Соединение с почтовым сервером зашифровано (TLS).
                С уважением, Система Персонального Электронного Документооборота!
                """,
                'nvo_blank.html',
                nvo_blank_related,
                f'app/templates/{current_user.tab_no}.pdf',
                settings,
            ))
            return templates.TemplateResponse(request=request, name='index_1.html', context={
                'title': redis_client.hget('suc_submit_page', 'title'),
                'message': redis_client.hget('suc_submit_page', 'message'),
            })
    except DataError:
        return templates.TemplateResponse(request=request, name='index_1.html', context={
            'title': redis_client.hget('empty_data_sent_error_page', 'title'),
            'message': redis_client.hget('empty_data_sent_error_page', 'message')
        })
    except TimeoutError:
        return {'message': 'Проверьте подключение к интернету'}
    except smtplib.SMTPServerDisconnected:
        return {'message': 'Проверьте подключение к интернету'}
