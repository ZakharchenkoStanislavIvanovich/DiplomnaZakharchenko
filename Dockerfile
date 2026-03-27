FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /usr/local/app/app/static/uploads && \
    mkdir -p /usr/local/app/instance && \
    chown -R 1000:1000 /usr/local/app/app/static/uploads && \
    chown -R 1000:1000 /usr/local/app/instance

RUN useradd -u 1000 app
USER app

EXPOSE 3000

CMD ["python", "run.py"]