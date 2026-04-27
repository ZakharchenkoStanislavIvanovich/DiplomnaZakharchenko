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

export MSYS_NO_PATHCONV=1

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}     ПРОТОКОЛ ЛОКАЛЬНОГО ОНОВЛЕННЯ ТА ТЕСТУВАННЯ    ${NC}"
echo -e "${BLUE}==================================================${NC}"

if [ -f .env ]; then
    set -a; source .env; set +a
else
    echo -e "${RED}ПОМИЛКА: Файл .env не знайдено${NC}"
    exit 1
fi

echo -e "\n${BLUE}ЕТАП 1: ПЕРЕЗАПУСК КОНТЕЙНЕРІВ ТА ЗБІРКА ОБРАЗІВ${NC}"
docker compose down --remove-orphans
docker compose up -d --build

echo -e "\n${BLUE}ЕТАП 2: ПЕРЕВІРКА ГОТОВНОСТІ БАЗИ ДАНИХ (PORT 5432)${NC}"
DB_READY=false
for i in {1..20}; do
    if docker compose exec -T backend python3 -c "import socket; socket.create_connection(('db', 5432), timeout=1)" &>/dev/null; then
        DB_READY=true
        echo -e "${GREEN}СТАН: База даних готова до роботи${NC}"
        break
    fi
    echo "Спроба $i: Очікування відповіді від db..."
    sleep 3
done

if [ "$DB_READY" != true ]; then 
    echo -e "${RED}ПОМИЛКА: Перевищено час очікування бази даних${NC}"
    exit 1 
fi

echo -e "\n${BLUE}ЕТАП 3: СИНХРОНІЗАЦІЯ СТРУКТУРИ БД (DB UPGRADE)${NC}"
docker compose exec -T backend flask db upgrade

echo -e "\n${BLUE}==================================================${NC}"
echo -e "${BLUE}          ЗВІТ ПРО АВТОМАТИЗОВАНІ ТЕСТИ           ${NC}"
echo -e "${BLUE}==================================================${NC}"

EXIT_CODE=0

run_test_group() {
    local id=$1
    local name=$2
    local path=$3

    echo -e "\n${BLUE}ГРУПА №$id: $name${NC}"
    echo -e "${BLUE}--------------------------------------------------${NC}"
    
    if docker compose exec -T backend sh -c "export PYTHONPATH=. && python3 -m pytest -v --tb=short $path"; then
        echo -e "${GREEN}РЕЗУЛЬТАТ ГРУПИ №$id: УСПІШНО (PASSED)${NC}"
    else
        echo -e "${RED}РЕЗУЛЬТАТ ГРУПИ №$id: ВИЯВЛЕНО НЕВІДПОВІДНОСТІ (FAILED)${NC}"
        EXIT_CODE=1
    fi
}

run_test_group "1" "ДОСТУПНІСТЬ, БД, СТАТИКА ТА КОНФІГУРАЦІЯ (SMOKE)" "tests/test_smoke.py"
run_test_group "2" "ЧАСОВІ ЛІМІТИ, ФОРМАТИ, КРИПТОГРАФІЯ ТА ВАЛІДАЦІЯ (UNIT)" "tests/test_units.py"
run_test_group "3" "СКРІЗНІ СЦЕНАРІЇ, ТРАНЗАКЦІЇ ТА ЦІЛІСНІСТЬ ДАНИХ (INTEGRATION)" "tests/test_integration.py"

echo -e "\n${BLUE}==================================================${NC}"
if [ "$EXIT_CODE" == "1" ]; then
    echo -e "${RED}ВИСНОВОК: ТЕСТУВАННЯ ЗАВЕРШЕНО З ПОМИЛКАМИ (ПЕРЕВІРТЕ ЛОГИ)${NC}"
    exit 1
else
    echo -e "${GREEN}ВИСНОВОК: ВСІ ЕТАПИ ТЕСТУВАННЯ ЗАВЕРШЕНО УСПІШНО (FULL GREEN)${NC}"
    echo -e "${GREEN}СТАН БАЗИ: ОЧИЩЕНО ТА ГОТОВО ДО РОБОТИ${NC}"
    echo -e "${GREEN}АДРЕСА РЕСУРСУ: http://localhost:3000${NC}"
    echo -e "${GREEN}ЧАС ЗАВЕРШЕННЯ: $(date +'%H:%M:%S')${NC}"
fi
echo -e "${BLUE}==================================================${NC}"