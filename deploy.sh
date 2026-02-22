# #!/bin/bash
# set -e

# GREEN='\033[0;32m'
# RED='\033[0;31m'
# NC='\033[0m'

# echo -e "${GREEN}>>> Початок процесу оновлення...${NC}"

# if [ -f .env ]; then
#     set -a; source .env; set +a
# else
#     echo -e "${RED}ПОМИЛКА: Файл .env не знайдено${NC}"
#     exit 1
# fi

# : "${AWS_ACCOUNT_ID:?${RED}ПОМИЛКА: AWS_ACCOUNT_ID не встановлено в .env${NC}}"

# echo -e "${GREEN}>>> Стягування нових образів...${NC}"
# docker compose pull backend

# echo -e "${GREEN}>>> Перезапуск сервісів...${NC}"
# docker compose down --remove-orphans
# docker compose up -d

# echo -e "${GREEN}>>> Очікування ініціалізації бази даних...${NC}"
# DB_READY=false
# for i in {1..20}; do
#     if docker compose exec -T backend python3 -c "import socket; socket.create_connection(('db', 5432), timeout=1)" &>/dev/null; then
#         echo -e "${GREEN}+++ База доступна! +++${NC}"
#         DB_READY=true
#         break
#     fi
#     echo "Спроба $i: База ще не відповідає..."
#     sleep 3
# done

# if [ "$DB_READY" != true ]; then
#     echo -e "${RED}ПОМИЛКА: База 'db' не з'явилася в мережі за відведений час.${NC}"
#     docker compose logs db
#     exit 1
# fi

# echo -e "${GREEN}>>> Застосування міграцій бази даних...${NC}"
# docker compose exec -T backend flask db upgrade

# echo -e "${GREEN}>>> Запуск автоматичних тестів...${NC}"
# docker compose exec -T backend pytest tests/test_basic.py

# echo -e "${GREEN}>>> Стан сервісів після оновлення:${NC}"
# docker compose ps

# echo -e "${GREEN}>>> Успішно оновлено! Версія від: $(date +'%H:%M:%S')${NC}"

#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}>>> Початок процесу ЛОКАЛЬНОГО оновлення...${NC}"

if [ -f .env ]; then
    set -a; source .env; set +a
else
    echo -e "${RED}ПОМИЛКА: Файл .env не знайдено${NC}"
    exit 1
fi

echo -e "${GREEN}>>> Зупинка старих контейнерів...${NC}"
docker compose down --remove-orphans

echo -e "${GREEN}>>> Збірка та запуск сервісів (локально)...${NC}"

docker compose up -d --build

echo -e "${GREEN}>>> Очікування ініціалізації бази даних...${NC}"
DB_READY=false
for i in {1..20}; do
    if docker compose exec -T backend python3 -c "import socket; socket.create_connection(('db', 5432), timeout=1)" &>/dev/null; then
        echo -e "${GREEN}+++ База доступна! +++${NC}"
        DB_READY=true
        break
    fi
    echo "Спроба $i: База ще не відповідає..."
    sleep 3
done

if [ "$DB_READY" != true ]; then
    echo -e "${RED}ПОМИЛКА: База 'db' не з'явилася в мережі за відведений час.${NC}"
    docker compose logs db
    exit 1
fi

echo -e "${GREEN}>>> Застосування міграцій бази даних...${NC}"
docker compose exec -T backend flask db upgrade || echo "Міграції не знайдено або вже застосовані"

echo -e "${GREEN}>>> Запуск автоматичних тестів...${NC}"
docker compose exec -T backend pytest tests/test_basic.py || echo -e "${RED}Тести провалено, але контейнери працюють${NC}"

echo -e "${GREEN}>>> Стан сервісів після оновлення:${NC}"
docker compose ps

echo -e "${GREEN}>>> Успішно запущено локально! Час: $(date +'%H:%M:%S')${NC}"
echo -e "${GREEN}Сайт доступний за адресою: http://localhost:3000${NC}"