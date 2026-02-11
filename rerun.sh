#!/bin/bash

check_error() {
    if [ $? -ne 0 ]; then
        echo "ПОМИЛКА: $1"
        exit 1
    fi
}

echo "--- Зупинка та запуск контейнерів... ---"
sudo docker compose down
sudo docker compose up -d --build
check_error "Docker Build"

echo "--- Очікування бази (10 сек)... ---"
sleep 10

echo "--- Застосування міграцій... ---"
sudo docker compose exec backend flask db upgrade
check_error "Database Migration"

echo "--- Запуск тестів... ---"
sudo docker compose exec backend pytest tests/test_basic.py
check_error "Tests Failed"

echo "--- Статус сервісів: ---"
sudo docker compose ps
echo "--- Успішно оновлено! Тести пройдено. ---"