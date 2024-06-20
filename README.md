# Foodgram

## Описание
Foodgram - это проект в котором пользователи могут делиться рецептами различных блюд, подписываться на авторов, чтобы отслеживать их рецепты. Любимые рецепты можно занести в избранное, чтобы не потерять их. Также на сайте доступен функционал списка покупок, можно добавить несколько рецептов в корзину, а после скачать уже упорядоченный список ингредиентов, для удобства покупки их в магазине. Для неавторизованных пользоватлей доступен функционал просмотра рецептов и отдельных авторов.
Проект реализован на нескольких докер контейнерах (фронтенд, бэкенд, nginx и база данных) которые объеденены в одну сеть для взаимодействия.

## Технологии
Бекэнд реализован с помощью: Python, Django, Django REST framework, Djoser, PostgreSQL, NGINX, Gunicorn, Docker.

## Как развернуть проект
```
1. Клонируем репозиторий (SSH)
git clone git@github.com:Tantal25/foodgram-project-react.git
```
```
2. Создаем и актививруем вирутальное окружение

python -m venv venv

Windows: source venv/Scripts/activate
Linux: source venv/bin/activate
```
```
3. Устанавливаем менеджер пактов pip и зависимости

python -m pip install --upgrade pip

Переходим в папку backend в терминале и выполняем команду

pip install -r requirements.txt
```
```
4. Создать файл .env в корневой директории проекта со следующими переменными

POSTGRES_DB           Имя базы данных
POSTGRES_USER         Имя пользователя в базе данных
POSTGRES_PASSWORD     Пароль пользователя в базе данных
DB_HOST               Имя Docker контейнера для БД
DB_PORT               Порт по которому можно обратиться к БД
ALLOWED_HOSTS         Адреса доступа к проекту
DEBUG                 Режим отладки серверка (True or False)
SECRET_KEY            Cекретный код проекта для settings
ENGINE                Тип базы данных для использования в проекте (сервер опробован на SQLite и PostgreSQL)
```
```
5. Создаем Docker контейнеры (вместо username - ваш логин на DockerHub)
Перейти в терминале в папку backend (из корневой директории команда cd backend)
docker build -t username/foodgram_backend .
Перейти в терминале в папку frontend (из корневой директории команда cd frontend)
docker build -t username/foodgram_frontend .
Перейти в терминале в папку infra (из корневой директории команда cd infra)
docker build -t username/foodgram_infra .
```
```
6. Выгрузить образы в DockerHub (вместо username - ваш логин на DockerHub)
docker push username/foodgram_backend
docker push username/foodgram_frontend
docker push username/foodgram_infra
```
```
7. Запустить проект в контейнерах
Перейти в папку infra (из корневой директории команда cd infra)
docker compose up --build
```
```
8. Запустить отдельный терминал, перейти в нем в проект в папку infra и из неe выполнить пункты 9, 10, 11
```
```
9. Выполнить миграции в отдельном терминале (из папки infra)

docker compose exec backend python manage.py migrate
```
```
10. Загрузить данные тегов и ингредиентов в БД 

docker compose exec backend python manage.py load_tags
docker compose exec backend python manage.py load_ingredients
```
```
11. Загрузить статику для проекта

docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r ./collected_static/. ./backend_static/static/
```

### Проект будет доступен по адресу:

http://127.0.0.1:8000/


### Примеры запросов к API
```
Регистрация нового пользователя
POST /api/users/
```
```
Получение токена
POST /api/auth/token/login/
```
```
Получение данных своей учетной записи
GET /api/users/me/
```
```
Получение страницы конкретного пользователя и списка всех пользователей
GET /api/users/id/
GET /api/users/
```
```
Подписаться на автора
POST /api/users/id/subscribe
```
```
Получить свои подписки
GET /api/users/subscriptions/
```
```
Получение списка тегов и конкретного тега
GET /api/tags/
GET /api/tags/id
```
```
Получение списка ингредиентов и конкретного ингредиента
GET /api/ingredients/
GET /api/ingredients/id
```
```
Создание, обновление и удаление рецепта
POST /api/recipes/
PATCH /api/recipes/id/
DELETE /api/recipes/id/
```
```
Получение рецепта и списка рецептов
GET /api/recipes/id/
GET /api/recipes/
```
```
Добавление рецепта в список покупок и удаление из списка покупок
POST /api/recipes/id/shopping_cart/
DELETE /api/recipes/id/shopping_cart/
```
```
Скачать список покупок
GET /api/recipes/download_shopping_cart/
```
```
Добавление рецепта в избранное и удаление из избранного
POST /api/recipes/id/favorite/
DELETE /api/recipes/id/favorite/
```

### Автор проекта: Трахимец Вадим (Tantal250@yandex.ru)
