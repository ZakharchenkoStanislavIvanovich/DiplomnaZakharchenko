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
    echo "ПОМИЛКА: AWS_ACCOUNT_ID не знайдено"
    exit 1
fi

echo "--- Зупинка та чистка (ECR: $ECR_REPOSITORY) ---"
sudo -E docker compose down --remove-orphans

echo "--- Стягування образу ---"
sudo -E docker compose pull backend
check_error "Docker Pull"

echo "--- Запуск системи ---"
sudo -E docker compose up -d
check_error "Docker Up"

echo "--- Очікування бази (10 сек)... ---"
sleep 10

echo "--- Застосування міграцій... ---"
sudo -E docker compose exec -T backend flask db upgrade
check_error "Database Migration"

echo "--- Запуск тестів... ---"
sudo -E docker compose exec -T backend pytest tests/test_basic.py
check_error "Tests Failed"

sudo docker compose ps
echo "--- Успішно оновлено! Версія: $(date) ---"