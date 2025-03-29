import redis
from dotenv import load_dotenv
from os import getenv


load_dotenv()

class RatholeDB():
    def __init__(self):
        self.red = redis.Redis(host="localhost",
                               port=int(getenv("REDIS_PORT")),
                               password=getenv("REDIS_PASSWORD"),
                               decode_responses=True, db=2)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
    

    def add_service(self, tunnel_id, content):
        self.red.set(tunnel_id, content, ex=int(getenv("TUNNEL_TTL")))

        if not self.get_version():
            self.red.set("version", 1)
        else:
            self.red.incr("version")


    def get_dump(self):
        all_keys = self.red.keys("*")
        
        dmp = ""
        for key in all_keys:
            if key != "version":
                tunnel_id = key
                tunnel_id = f"[server.services.{tunnel_id}]"

                content = self.red.get(key)

                dmp += f"{tunnel_id}\n{content}\n\n"

        return dmp


    def delete_sevice(self, tunnel_id):
        self.red.delete(tunnel_id)


    def get_ttl(self, tunnel_id):
        return self.red.ttl(tunnel_id)


    def get_version(self):
        return self.red.get("version")


    def close(self):
        self.red.close()

