#!/bin/bash

check_error() {
    if [ $? -ne 0 ]; then
        echo "ПОМИЛКА: $1"
        exit 1
    fi
}

echo "--- Зупинка та запуск... ---"
sudo docker compose down
sudo docker compose up -d --build
check_error "Docker Build"

echo "--- Очікування бази... ---"
sleep 7

echo "--- Створення таблиць... ---"
sudo docker compose exec backend python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
check_error "Database Migration"

echo "--- Запуск тестів... ---"
sudo docker compose exec backend pytest tests/test_basic.py
check_error "Tests Failed"

echo "--- Статус сервісів: ---"
sudo docker compose ps
echo "--- Успішно оновлено! Тести пройдено. ---"