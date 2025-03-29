from mailtunnel.database.rathole_config_db import *
from time import sleep
from dotenv import load_dotenv
from os import getenv
from os.path import dirname
import logging


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

def main():
    _logger.info("Started...")
    with RatholeDB() as r_db:
        prev_version = r_db.get_version()

        while True:
            if r_db.get_version() == prev_version:
                continue

            _logger.info("Config updated")
            
            path_to_conf = dirname(__file__) + "/rathole/config.toml"

            with open(path_to_conf, "w") as conf:
                pre = """[server]
bind_addr = \"0.0.0.0:6789\"

[server.services.test]
bind_addr = \"127.0.0.0:5432\"
token = \"5432\"

"""
                conf.write(pre + r_db.get_dump())

            sleep(int(getenv("RATHOLE_CONFIG_UPDATE")))

if __name__ == "__main__":
    main()
