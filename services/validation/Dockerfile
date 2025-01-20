# services/validation/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY services/validation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/validation/app/ /app/app/

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main"]