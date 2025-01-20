# services/upload/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY services/upload/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/upload/app/ /app/app/

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main"]