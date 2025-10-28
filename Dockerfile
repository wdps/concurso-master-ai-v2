﻿FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD gunicorn --bind 0.0.0.0:8080 app:app --workers 1 --threads 2 --timeout 120
