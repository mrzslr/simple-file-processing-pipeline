# services/validation/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY services/notification/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/notification/app/ /app/app/

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main"]