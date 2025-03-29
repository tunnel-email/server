from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_sso.sso.yandex import YandexSSO

from starlette.requests import Request
from starlette.status import *

from mailtunnel.database.user_db import *
from mailtunnel.database.routing_db import *
from mailtunnel.database.rathole_config_db import *
from mailtunnel.api.schemas import *
from mailtunnel.api.utils import *
from mailtunnel.api.dns import *

import logging
from secrets import token_hex
from pydantic import BaseModel
from uuid import uuid4
import asyncio

from dotenv import load_dotenv
from os import getenv


_logger = logging.getLogger(__name__)


load_dotenv()

app = FastAPI()

yandex_sso = YandexSSO(
    client_id=getenv("YANDEX_CLIENT_ID"),
    client_secret=getenv("YANDEX_CLIENT_SECRET"),
    redirect_uri=getenv("YANDEX_REDIRECT_URI"),
    scope=[""]
)

states = {}


@app.get("/auth/yandex/login")
async def yandex_login(token: str):
    state = generate_secret(25)
    states[state] = token

    async with yandex_sso:
        return await yandex_sso.get_login_redirect(state=state)


@app.get("/auth/yandex/callback")
async def yandex_callback(request: Request):
    state = request.query_params["state"]
    user_token = states[state]

    del states[state]

    async with yandex_sso:
        user = await yandex_sso.verify_and_process(request)

    with Database() as db:
        if not db.user_exists(user.id):
            _logger.info(f"New user registered: {user.id}")

        if not db.token_is_taken(user_token):
            max_token_count = int(getenv("MAX_TOKEN_COUNT"))

            if db.number_of_tokens(user.id) < max_token_count:
                db.add_token(user.id, user_token) # adding user to the database
            else:
                raise HTTPException(HTTP_403_FORBIDDEN, detail=f"Maximum number of tokens is {max_token_count}")
        else:
            raise HTTPException(HTTP_409_CONFLICT, detail="Token is already taken")

        _logger.info(f"{user.id} got new token")

    return "Пользователь подтверждён. Можете закрыть вкладку"


@app.post("/create_tunnel")
async def create_tunnel(token: Token):
    with Database() as db:
        user_id = db.get_id_by_token(token.token)
        _logger.info(f"User_id {user_id} wants to create a tunnel")
        
    if not user_id:
        _logger.debug(f"Invalid token: {token.token}")
        raise HTTPException(HTTP_403_FORBIDDEN, detail=f"Invalid token: {token.token}")

    with RoutingDB() as r_db:
        if r_db.get_current_tunnel(token.token):
            _logger.debug(f"User {user_id} requested for an extra tunnel")

            raise HTTPException(HTTP_409_CONFLICT, detail="Tunnel has been already created")
        

    tunnel_id = generate_secret(int(getenv("TUNNEL_ID_LENGTH")))
    tunnel_secret = generate_secret(int(getenv("TUNNEL_SECRET_LENGTH")))

    subdomain = generate_secret(int(getenv("SUBDOMAIN_LENGTH")))

    # Creating new tunnel
    port = new_tunnel(tunnel_id, tunnel_secret, subdomain)
    # TODO: new_tunnel should handle all this
    with RoutingDB() as r_db:
        r_db.set_tunnel(token.token, subdomain, tunnel_id)

    # Adding MX DNS record
    # mx_result = add_mx(subdomain)

    # Adding A DNS record
    # a_result = add_alias(subdomain)

    # Adding MTA-STS DNS record
    # mta_sts_result = add_mta_sts(subdomain)

    
    # If adding MX was unsuccessful:
    # if not mx_result:
    #     delete_current_tunnel(token.token)
    #     return HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create MX")

    # # If adding A was unsuccessful:
    # if not a_result:
    #     delete_current_tunnel(token.token)
    #     return HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create A")

    # If adding MTA-STS was unsuccessful:
    # if not mta_sts_result:
    #     delete_current_tunnel(token.token)
    #     raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create MTA-STS")

    _logger.info(f"Tunnel was created by {user_id}")

    return {"subdomain": f"{subdomain}.aist.site", "tunnel_id": tunnel_id, "tunnel_secret": tunnel_secret}


@app.post("/delete_tunnel")
async def delete_tunnel(token: Token):
    with Database() as db:
        user_id = db.get_id_by_token(token.token)
        _logger.info(f"User_id {user_id} wants to delete a tunnel")
        
    if not user_id:
        _logger.debug(f"Invalid token: {token.token}")
        raise HTTPException(HTTP_403_FORBIDDEN, detail=f"Invalid token: {token.token}")
        HTTP_404_NOT_FOUND

    return delete_current_tunnel(token.token)


@app.post("/verify_subdomain")
async def verify_subdomain(data: HTTP01_Data):
    with Database() as db:
        user_id = db.get_id_by_token(data.token)
        _logger.info(f"User_id {user_id} wants to create a tunnel")

    if not user_id:
        _logger.debug(f"Invalid token: {data.token}")
        raise HTTPException(HTTP_403_FORBIDDEN, detail=f"Invalid token: {data.token}")
    
    with RoutingDB() as routing_db:
        tunn = routing_db.get_current_tunnel(data.token)

        if tunn:
            subdomain = tunn[0]
            domain = getenv("DOMAIN")
            expected_subdomain = f"{subdomain}.{domain}"
        else:
            raise HTTPException(HTTP_403_FORBIDDEN, detail="No active tunnels")

    @temporary_route(app, f"/.well-known/acme-challenge/{data.url_token}",
                     int(getenv("HTTP01_URL_TTL")), expected_subdomain)
    async def handle_http01():
        return Response(
            content=data.validation_token,
            media_type="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=resp.txt"
            }
        )

    return {"Successfuly started HTTP01 challenge"}


@app.get("/tunnel_status")
async def tunnel_status(tunnel_id: str):
    tunnel_id = tunnel_id.lower()

    if not is_correct_tunnel_id(tunnel_id):
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid tunnel_id")
    
    with RatholeDB() as r_db:
        ttl = r_db.get_ttl(tunnel_id)

    return {"ttl": ttl}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)
