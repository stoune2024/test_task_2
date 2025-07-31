FROM python:3.12-slim
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
WORKDIR /test_task_2
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini .env ./
COPY ./app ./app
EXPOSE 8000
USER appuser
CMD alembic upgrade head
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
