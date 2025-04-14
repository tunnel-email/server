from mailtunnel.database.rathole_config_db import *
from time import sleep
from dotenv import load_dotenv
from os import getenv
import logging


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

RATHOLE_CONFIG = "/etc/rathole/mailtunnel-config.toml"

def main():
    _logger.info("Started...")

    with RatholeDB() as r_db:
        prev_version = r_db.get_version()

        while True:
            if r_db.get_version() == prev_version:
                continue

            _logger.info("Config updated")

            with open(RATHOLE_CONFIG, "w") as conf:
                pre = """[server]
bind_addr = \"0.0.0.0:6789\"

[server.services.test]
bind_addr = \"127.0.0.0:5432\"
token = \"5432\"

"""
                conf.write(pre + r_db.get_dump())

            prev_version = r_db.get_version()

            sleep(int(getenv("RATHOLE_CONFIG_UPDATE")))

if __name__ == "__main__":
    main()
