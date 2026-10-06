FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements-api.txt ./backend/requirements-api.txt

RUN pip install --no-cache-dir -r backend/requirements-api.txt

COPY backend ./backend

COPY data/database ./data/database

WORKDIR /app/backend

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]