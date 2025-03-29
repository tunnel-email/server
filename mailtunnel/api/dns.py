import requests
import json
import logging

from dotenv import load_dotenv
from os import getenv

from mailtunnel.api.utils import generate_secret

load_dotenv()

_logger = logging.getLogger(__name__)

ENDPOINT = "https://api.reg.ru/api/regru2/zone"

def generic_request(operation, additional_data):
    input_data = {
        "username": getenv("REGRU_USERNAME"),
        "password": getenv("REGRU_PASSWORD"),
        "domains": [{"dname": getenv("DOMAIN")}],
        "output_content_type": "plain"
    }
    input_data |= additional_data

    req = requests.post(f"{ENDPOINT}/{operation}", data={
        "input_data": json.dumps(input_data),
        "input_format": "json"
    })

    req_json = req.json()

    if req_json["answer"]["domains"][0]["result"] == "success":
        return True
    else:
        _logger.error(f"Unable to create perform /{operation}: {req_json}")
        return False


def add_mta_sts(subdomain):
    mta_sts_id = generate_secret(32)
    add_data = {
        "subdomain": f"_mta_sts.{subdomain}",
        "text": f"v=STSv1; id={mta_sts_id};"
    }

    return generic_request("add_txt", add_data)

def add_mx(subdomain):
    add_data = {
        "subdomain": subdomain,
        "priority": 0,
        "mail_server": subdomain
    }

    return generic_request("add_mx", add_data)

def add_alias(subdomain):
    add_data = {
        "subdomain": subdomain,
        "ipaddr": getenv("IP")
    }

    return generic_request("add_alias", add_data)
