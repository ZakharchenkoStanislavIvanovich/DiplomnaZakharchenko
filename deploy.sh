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

echo "--- Очікування бази (30 сек)... ---"
sleep 30

echo "--- Застосування міграцій... ---"
sudo docker compose --env-file .env exec -T backend flask db upgrade
check_error "Database Migration"

echo "--- Запуск тестів... ---"
sudo docker compose --env-file .env exec -T backend pytest tests/test_basic.py
check_error "Tests Failed"

sudo docker compose --env-file .env ps
echo "--- Успішно оновлено! Версія: $(date) ---"