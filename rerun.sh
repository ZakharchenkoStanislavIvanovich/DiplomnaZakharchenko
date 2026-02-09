#!/bin/bash

echo "--- Зупинка та очищення старих контейнерів... ---"
sudo docker compose down

echo "--- Збірка та запуск PostgreSQL та Backend... ---"
sudo docker compose up -d --build

echo "--- Очікування готовності PostgreSQL (7 секунд)... ---"
sleep 7

echo "--- Створення таблиць у PostgreSQL... ---"
sudo docker compose exec backend python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"

echo "--- Статус сервісів: ---"
sudo docker compose ps

echo "--- Готово! Адмін: admin / admin123 ---"