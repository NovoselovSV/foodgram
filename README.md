# Foodgram
[![Main Foodgram workflow](https://github.com/NovoselovSV/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/NovoselovSV/foodgram/actions/workflows/main.yml)
## Описание
Проект реализует кодовую базу и возможность контейнерного развертывания сайта [Foodgram](https://oxo-diplom.mooo.com), а так же его CI/CD составляющую.
## Установка
1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/NovoselovSV/foodgram.git
```
```
cd foodgram
```

### Для развертывания в Docker
1. Скачайте и установите [Docker](https://www.docker.com/) с официального сайта в соответствии с вашей ОС.
2. Перейдите в папку infra
```
cd infra
```
3. Создейте файл .env в который поместите следующее содержание, заменяя угловые скобки (<>) и то что в них на соответствующие значения.
```
POSTGRES_DB=<Название бд в PostgresDB (например kittygram)>
POSTGRES_USER=<Username суперпользователя для контейнера PostgresDB (например kittygram_user)>
POSTGRES_PASSWORD=<Пароль суперпользователя для POSTGRES_USER>
DB_HOST=<Адрес по которому бэкенд будет соединяться с базой данных (допустимо имя контейнера 'db' без ковычек)>
DB_PORT=<Порт DB_HOST (стандартный порт 5432)>
SECRET_KEY=<Секретный ключ для работы Django (можно получить по адресу https://djecrety.ir/)>
ALLOWED_HOSTS=<Хосты, на которых допустима работа бэкенда, перечисляются через пробел (на локальной машине можно установать 'localhost 127.0.0.1' без ковычек, или удалить данную строку, в последнем случае будут допустимы любые хосты - '*')>
```
4. Запустить развертывание:
- локальных контейнеров (при необходимости добавить ключ `--build`)
```
sudo docker compose up
```
- официальных контейнеров из DockerHub
```
sudo docker compose -f docker-compose.production.yml up
```
4. Провести Django миграции, собрать статику бэкенда и доставить ее в доступную для nginx папку
```
sudo docker compose [-f docker-compose.production.yml] exec backend python manage.py migrate
sudo docker compose [-f docker-compose.production.yml] exec backend python manage.py collectstatic
sudo docker compose [-f docker-compose.production.yml] exec backend cp -r /app/collected_static/. /backend_static/static/
``` 
В той же папке при желании и использовании ОС Linux можно воспользоваться скриптами after\_start\_local и after\_start\_production, которые сделают вышеуказанные операции за вас, а также импортируют заранее созданные ингредиенты и начнут создавать суперпользователя.
### Для изменения кода Django приложения
1. Перейти в директорию backend
```
cd backend
```
2. Cоздать и активировать виртуальное окружение
```
python3 -m venv env
```
```
source env/bin/activate
```
3. Установить зависимости из файла requirements.txt
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
## Примеры запросов к бэкенду
1. POST /api/users/
```
{

    "email": "vpupkin@yandex.ru",
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Иванов",
    "password": "Qwerty123"

}
```
Response
```
{
    "email": "vpupkin@yandex.ru",
    "id": 1,
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Иванов"
}
```
2. POST /api/token/login/
```
{

    "password": "string",
    "email": "vpupkin@yandex.ru"

}
```
Response
```
{
    "auth_token":"0123456789absdef0123456789abcdef01234567"
}
```
3. GET /api/users/me/
Response
```
{

    "email": "vpupkin@yandex.ru",
    "id": 1,
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Иванов",
    "is_subscribed": false,
    "avatar": "http://foodgram.example.org/media/users/image.png"

}
```
## Использованые технологии
1. Docker - система контейнеризации (https://www.docker.com/)
2. Django - фреймворк бэкенда (https://www.djangoproject.com/)
3. DRF - фреймворк-надстройка над Django для создания REST API (https://www.django-rest-framework.org/)
4. Node.js - фреймворк, среда выполнения для фронтэнда (https://nodejs.org/en)
5. Git - система контроля версий (https://git-scm.com/)
6. GitHubActions - система для осуществления CI/CD в GitHub (https://docs.github.com/ru/actions)
## Автор
[Новоселов Сергей](https://github.com/NovoselovSV) и команда [Яндекс практикума](https://github.com/yandex-praktikum)

