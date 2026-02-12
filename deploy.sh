#!/bin/bash

check_error() {
    if [ $? -ne 0 ]; then
        echo "ПОМИЛКА: $1"
        exit 1
    fi
}

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "ПОМИЛКА: AWS_ACCOUNT_ID не знайдено в .env"
    exit 1
fi

echo "--- Зупинка та чистка (ECR: $ECR_REPOSITORY) ---"
sudo docker compose --env-file .env down --remove-orphans

echo "--- Стягування образу ---"
sudo docker compose --env-file .env pull backend
check_error "Docker Pull"

echo "--- Запуск системи ---"
sudo docker compose --env-file .env up -d
check_error "Docker Up"

echo "--- Чекаємо на старт бази (TCP Check) ---"
DB_READY=false
for i in {1..30}; do
  if sudo docker compose --env-file .env exec -T backend python3 -c "import socket; socket.create_connection(('db', 5432), timeout=1)" 2>/dev/null; then
    echo "+++ БАЗА ЗНАЙДЕНА І ДОСТУПНА! (спроба $i) +++"
    DB_READY=true
    break
  fi
  echo "База ще не відповідає (спроба $i)..."
  sleep 2
done

if [ "$DB_READY" = false ]; then
    echo "ПОМИЛКА: База 'db' не з'явилася в мережі за 60 секунд."
    sudo docker compose --env-file .env logs db
    exit 1
fi

echo "--- Застосування міграцій ---"
sudo docker compose --env-file .env exec -T backend flask db upgrade
check_error "Database Migration"

echo "--- Запуск тестів... ---"
sudo docker compose --env-file .env exec -T backend pytest tests/test_basic.py
check_error "Tests Failed"

sudo docker compose --env-file .env ps
echo "--- Успішно оновлено! Версія: $(date) ---"