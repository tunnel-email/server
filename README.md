# readme

## Настройка
1. Установить зависимости: `sudo apt install python3-pip mysql-server redis pkg-config default-libmysqlclient-dev wget unzip nginx` 
2. Установить пакет
```bash
pip install . # сначала так
pip install -e . # потом так
```
3. Установить rathole
```bash
sudo ./setup_rathole.sh
```
4. Создать БД mysql через код в `db_create.sql`. Заменить `strong_password` на надёжный пароль 
5. Получить `client_id`, `client_secret` для Yandex OAuth
6. Создать `.env` в соответсвии с данным шаблоном:

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
YANDEX_REDIRECT_URI= # https://<your-domain>/auth/yandex/callback

REGRU_USERNAME= # not necessary for now
REGRU_PASSWORD= # not necessary for now

SUBDOMAIN_LENGTH= # on main instance: 25
TUNNEL_SECRET_LENGTH= # on main instance: 25
TUNNEL_ID_LENGTH= # on main instance: 25
TUNNEL_TTL= # on main instance: 900 = 15 min
HTTP01_URL_TTL= # on main instance: 90 = 1.5 min
```
7. Выдать права python на работу с root портами (нужно для mailtunnel-forwarder): `sudo setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))`
7. Убедиться, что присутствует A запись в DNS на поддомен * 

## Запуск
Сервер состоит из 4 основных компонентов:
* `rathole` - менеджер туннелей
* `mailtunnel-confdumper` - дампер текущих туннелей в конфиг rathole
* `mailtunnel-forwarder` - маршрутизатор электронных писем на основе SNI
* `mailtunnel-api` - API для работы с сервисом

### Самый простой способ запуска
Запустите в нескольких сессиях:
```bash
rathole /etc/rathole/mailtunnel-config
```
```bash
mailtunnel-confdumper
```
```bash
mailtunnel-forwarder
```
```bash
mailtunnel-api
```

### Рекомендуемый способ запуска
Рекомендуется создать для каждого компонента systemd сервис.
Подробная инструкция находится <a href="systemd/README.md">здесь</a>

> NOTE: предварительно убедитесь, что запущены БД MySQL и Redis

## Настройка HTTPS
1. Установите nginx
2. Получите TLS сертификат:
```bash
sudo certbot --nginx -d <your-domain> -d www.<your-domain>
```
3. Поместите конфигурацию из `nginx-conf/tunnel.email` в `/etc/nginx/sites-available/`
```bash
sudo cp ./nginx-conf/tunnel.email /etc/nginx/sites-available/
```
4. Замените tunnel.email на ваш домен в конфигурации
5. Удалите `/etc/nginx/sites-enabled/default`
```bash
sudo rm /etc/nginx/sites-enabled/default
```
5. Создайте ссылку на конфигурацию в `/etc/nginx/sites-enabled/`
```bash
sudo ln -s /etc/nginx/sites-available/tunnel.email /etc/nginx/sites-enabled/
```
