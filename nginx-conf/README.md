# nginx конфигурация

Данная конфигурация реализует HTTPS для `tunnel.email`/`www.tunnel.email` и HTTP для всех остальных поддоменов. Это нужно для того, чтобы доступ к основному содержимому был организован через HTTPS, а на остальных поддоменах работал бы HTTP01 Challenge.

Получите сертификат Let's Encrypt, замените `tunnel.email` на ваш домен и разместите конфигурацию в `/etc/nginx/sites/available/<your-domain>`. Создайте ссылку на него в `/etc/nginx/sites/enabled/<your-domain>`