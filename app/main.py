from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from os.path import relpath
import time

from app.routers.routs import router as routs_router, templates
from app.routers.db import router as db_router
from app.routers.safety import router as safety_router
from app.routers.logs import main_logger

app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Метла, добавляющая заголовок, показывающий время, за которое обработался эндпоинт
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    main_logger.info(f'It took {str(process_time)} seconds to respond')
    return response


@app.middleware("http")
async def log_tracking_func(request: Request, call_next):
    """
    Метла, логирующая информацию о клиентах
    """
    # Log request details
    client_ip = request.client.host
    client_port = request.client.port
    method = request.method
    url = request.url.path
    main_logger.info(f'Request: {method} {url} from {client_ip}:{client_port}')
    # Process the request
    response = await call_next(request)
    # Log response details
    status_code = response.status_code
    main_logger.info(f'Response: {method} {url} returned {status_code} to {client_ip}:{client_port}')
    return response


app.include_router(routs_router)
app.include_router(db_router)
app.include_router(safety_router)

app.mount('/static_files', StaticFiles(directory=relpath(f'{relpath(__file__)}/../static')), name='static')


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 401:
        return templates.TemplateResponse(
            request=request,
            name="401_error.html",
            status_code=exc.status_code,
            headers=exc.headers,
        )
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request=request,
            name="404_error.html",
            status_code=exc.status_code,
            headers=exc.headers,
        )
