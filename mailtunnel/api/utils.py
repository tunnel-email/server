from secrets import choice
from string import ascii_lowercase, digits, hexdigits
from portpicker import pick_unused_port
import asyncio

from fastapi import Depends, HTTPException, Request, Response
from starlette.status import *

from mailtunnel.database.rathole_config_db import *
from mailtunnel.database.routing_db import *

from dotenv import load_dotenv
from os import getenv

import logging

_logger = logging.getLogger(__name__)

load_dotenv()

def generate_secret(length):
    return ''.join(choice(ascii_lowercase + digits) for i in range(length))


def is_correct_tunnel_id(tunnel_id):
    if len(tunnel_id) != int(getenv("TUNNEL_ID_LENGTH")):
        return False
    
    for i in tunnel_id:
        alph = ascii_lowercase + digits
        if i not in alph:
            return False

    return True


def new_tunnel(tunnel_id, secret_token, subdomain):
    free_port = pick_unused_port()

    text = f"""token = \"{secret_token}\"
bind_addr = \"127.0.0.1:{free_port}\""""

    with RoutingDB() as route_db:
        route_db.add_route(subdomain, free_port)

    with RatholeDB() as r_db:
        r_db.add_service(tunnel_id, text)
    
    return free_port


def subdomain_check(expected_subdomain: str):
    def check(request: Request):
        host = request.headers.get("host", "")

        if not host:
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="Host header missing")
        
        host = host.split(":")[0]

        if host != expected_subdomain:
            raise HTTPException(HTTP_404_NOT_FOUND, detail="Not found")

        return True
    
    return check


def temporary_route(app, path: str, duration: int, subdomain: str):
    def decorator(func):
        async def wrapper():
            app.add_api_route(path, func, dependencies=[Depends(subdomain_check(subdomain))])
            await asyncio.sleep(duration)
            app.router.routes = [route for route in app.router.routes if route.path != path]
        
        asyncio.create_task(wrapper())
        return func
    
    return decorator


def delete_current_tunnel(token):
    with RoutingDB() as r_db:
        tunn = r_db.get_current_tunnel(token)
        
        if not tunn:
            return {"Tunnel has been already deleted"}

        subdomain, tunnel_id = tunn

        r_db.delete_route(subdomain)
        r_db.delete_tunnel(token)

    with RatholeDB() as rathole_db:
        rathole_db.delete_sevice(tunnel_id)

    return {"Successfuly deleted tunnel"}

