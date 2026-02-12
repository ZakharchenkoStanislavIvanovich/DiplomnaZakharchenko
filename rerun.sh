#!/bin/bash

check_error() {
    if [ $? -ne 0 ]; then
        echo "ПОМИЛКА: $1"
        exit 1
    fi
}

echo "--- Зупинка та запуск контейнерів (чистий запуск з ECR) ---"
sudo docker compose down

sudo docker compose pull backend
check_error "Docker Pull"

sudo docker compose up -d
check_error "Docker Up"

echo "--- Очікування бази (10 сек)... ---"
sleep 10

echo "--- Застосування міграцій... ---"
sudo docker compose exec -T backend flask db upgrade
check_error "Database Migration"

echo "--- Запуск тестів... ---"
sudo docker compose exec -T backend pytest tests/test_basic.py
check_error "Tests Failed"

echo "--- Статус сервісів: ---"
sudo docker compose ps
echo "--- Успішно оновлено! Тести пройдено. ---"