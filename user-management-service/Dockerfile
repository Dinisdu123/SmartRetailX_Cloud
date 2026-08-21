FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Install requirements with explicit package
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir prometheus-fastapi-instrumentator==6.1.0

COPY app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]