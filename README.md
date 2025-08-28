## Installation

1. Clone the repository:

git clone https://github.com/adamkhaydaev/project.git
cd project
Install dependencies with uv:

<<<<<<< HEAD
pip install uv
uv sync
Run the application:

uvicorn app.main:app --reload"# project1" 
"# project1" 
=======
# Перейдите в папку проекта
cd C:\Users\ВашеИмя\Downloads\project-main

# Установите зависимости
pip install fastapi uvicorn sqlalchemy

Создание тестового пользователя

# Запустите скрипт создания пользователя
python app/create_user_simple.py
Запуск сервера

# Запуск из папки app
cd app
uvicorn simple_app:app --reload

# Или запуск из корневой папки
uvicorn app.simple_app:app --reload

Проверка работы
Откройте в браузере: http://127.0.0.1:8000
Документация API: http://127.0.0.1:8000/docs

📊 API Endpoints

Публичные эндпоинты
GET / - Информация о сервисе
GET /{alias} - Перенаправление по короткой ссылке
GET /health - Проверка здоровья сервиса
POST /register - Регистрация нового пользователя

Приватные эндпоинты (требуют Basic Auth)
POST /urls/ - Создание короткой ссылки
GET /urls/ - Получение списка всех ссылок
POST /urls/{id}/deactivate - Деактивация ссылки
GET /stats/detailed/ - Расширенная статистика переходов

🔐 Аутентификация

Используется Basic Authentication. Для доступа к приватным эндпоинтам добавьте заголовок:
text
Authorization: Basic base64(username:password)

Тестовый пользователь:
Логин: admin
Пароль: password

🛠 Использование

Создание пользователя
curl -X POST "http://127.0.0.1:8000/register/?username=myuser&password=mypassword"

Создание короткой ссылки
curl -X POST "http://127.0.0.1:8000/urls/" \
  -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/very/long/url", "expiration_days": 30}'

Получение статистики
curl -X GET "http://127.0.0.1:8000/stats/detailed/" \
  -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ="

Перенаправление по короткой ссылке
curl -X GET "http://127.0.0.1:8000/abc123"

⚙️ Настройки
База данных: SQLite (файл test.db в корневой папке)
Порт: 8000
Длина имени: 8 символов (по умолчанию)
Время жизни ссылки: 30 дней (по умолчанию)

🐛 Устранение проблем
Ошибка импорта модулей
Убедитесь, что запускаете из правильной папки:

# Правильно - из корневой папки
cd C:\Users\ВашеИмя\Desktop\my_project
uvicorn app.simple_app:app --reload
# Или из папки app
cd app
uvicorn simple_app:app --reload

Ошибка базы данных
Удалите файл test.db для пересоздания базы данных.

📦 Зависимости
fastapi==0.104.1 - Web фреймворк
uvicorn==0.24.0 - ASGI сервер
sqlalchemy==2.0.23 - ORM для работы с БД

📝 Лицензия
MIT License
>>>>>>> 29e030a8c213cac20fd4f867d8dab73068c5a521
"# project1" 
"# project1" 
"# project1" 
