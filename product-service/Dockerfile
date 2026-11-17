FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=5002

WORKDIR /app

# Instala dependências de sistema para o driver ODBC (SQL Server / Azure SQL Database)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "2", "--threads", "4", "app:app"]
