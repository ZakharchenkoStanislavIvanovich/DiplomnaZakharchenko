#!/bin/bash

echo "--- Зупинка поточних контейнерів... ---"
docker compose down

echo "--- Збірка образів та запуск сервісів... ---"

docker compose up -d --build

echo "--- Очікування запуску бази даних (3 сек)... ---"
sleep 3

echo "--- Створення таблиць та заповнення даними... ---"
# Ініціалізація
docker compose exec backend python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
docker compose exec backend python seed.py

echo "--- Статус контейнерів: ---"
docker compose ps

echo "--- Проект NotaryApp успішно перезапущений на порті 3000! ---"