import redis
from os import getenv
from dotenv import load_dotenv


load_dotenv()

class RoutingDB():
    def __init__(self):
        self.red = redis.Redis(host="localhost",
                               port=int(getenv("REDIS_PORT")),
                               password=getenv("REDIS_PASSWORD"),
                               decode_responses=True, db=0)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
    

    def add_route(self, subdomain, port):
        self.red.set(subdomain, port, ex=int(getenv("TUNNEL_TTL")))


    def set_tunnel(self, token, subdomain, tunnel_id):
        self.red.set(f"token:{token}", f"{subdomain}|{tunnel_id}", ex=int(getenv("TUNNEL_TTL")))
    

    def get_current_tunnel(self, token):
        tunn = self.red.get(f"token:{token}")
        
        if tunn:
            subdomain, tunnel_id = tunn.split("|")
        
            return subdomain, tunnel_id
        else:
            return None


    def delete_route(self, subdomain):
        self.red.delete(subdomain)

    
    def delete_tunnel(self, token):
        self.red.delete(f"token:{token}")


    def get_port_by_subdomain(self, subdomain):
        return self.red.get(subdomain)


    def close(self):
        self.red.close()

