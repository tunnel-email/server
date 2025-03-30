#!/bin/bash

wget "https://github.com/rapiz1/rathole/releases/download/v0.4.8/rathole-x86_64-unknown-linux-gnu.zip" &&

unzip rathole-x86_64-unknown-linux-gnu.zip &&
rm rathole-x86_64-unknown-linux-gnu.zip &&

mv rathole /usr/bin/ &&

mkdir -p /etc/rathole &&
echo -e '[server]\nbind_addr = "0.0.0.0:6789"\n\n[server.services.test]\nbind_addr = "127.0.0.0:5432"\ntoken = "5432"' > \
/etc/rathole/mailtunnel-config.toml &&

chmod 600 /etc/rathole/mailtunnel-config.toml 
