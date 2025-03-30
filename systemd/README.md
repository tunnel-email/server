# systemd сервисы

Отредактируйте каждую из конфигураций в данной папке в соответствии с вашими системными настройками. Менять стоит только параметры, помеченные комментарием.

После этого, выполните следующие команды:
```bash
sudo cp mailtunnel-*.service /etc/systemd/system/
sudo cp ratholes.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable mailtunnel-forwarder.service
sudo systemctl enable mailtunnel-api.service
sudo systemctl enable mailtunnel-confdumper.service
sudo systemctl enable ratholes.service

sudo systemctl start mailtunnel-forwarder.service
sudo systemctl start mailtunnel-api.service
sudo systemctl start mailtunnel-confdumper.service
sudo systemctl start ratholes.service
```

Теперь вы можете использовать стандартные инструменты systemd для управления mailtunnel
