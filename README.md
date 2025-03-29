# readme

## Настройка
1. Установить зависимости
```bash
pip install -r requirements.txt
```
2. Установить базы данных MySQL, Redis
3. Создать БД mysql через код в db_create.sql. Заменить strong_password на надёжный пароль
4. Получить client_id, client_secret для Yandex OAuth
5. Создать .env в соответсвии с данным шаблоном:

```bash
DOMAIN= # your domain name
IP= # ip address of your server

REDIS_PASSWORD=
REDIS_PORT=

MYSQL_PASSWORD=
MYSQL_PORT=

TOKEN_LENGTH= # on main instance: 40
MAX_TOKEN_COUNT= # on main instance: 3

RATHOLE_CONFIG_UPDATE= # on main instance: 5

YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
YANDEX_REDIRECT_URI=

REGRU_USERNAME= # not necessary. for future plans
REGRU_PASSWORD= # not necessary. for future plans

SUBDOMAIN_LENGTH= # on main instance: 25
TUNNEL_SECRET_LENGTH= # on main instance: 25
TUNNEL_ID_LENGTH= # on main instance: 25
TUNNEL_TTL= # on main instance: 900 = 15 min
HTTP01_URL_TTL= # on main instance: 90 = 1.5 min
```

## Запуск
Сервер состоит из 4 основных компонентов:
* rathole - менеджер туннелей
* config_dumper - дампер текущих туннелей в конфиг rathole
* sni_forwarder - маршрутизатор электронных писем на основе SNI
* http_api - API для работы с сервисом

Запустите в нескольких сессиях:
```bash
./rathole config.toml
```
```bash
python -m mailtunnel.config_dumper
```
```bash
python -m mailtunnel.sni_forwarder
```
```bash
python -m mailtunnel.http_api
```

> NOTE: предварительно убедитесь, что запущены БД MySQL и Redis