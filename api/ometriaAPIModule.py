import os

import requests
from typing import List

from api.requestsModule import APIRequestError, make_request
from classes.ometriaMember import OmetriaMember
from logger.loggingModule import logger


# Retrieve the Mailchimp API key from an environment variable
OMETRIA_API_KEY = os.getenv("OMETRIA_API_KEY")

# Check if the environment variable is set and handle the case if it's not
if OMETRIA_API_KEY is None:
    raise ValueError("OMETRIA_API_KEY environment variable is not set")

OMETRIA_BASE_URL = "https://api-demo-ingest.ew1-prod.ew1.prod.ometria.cloud/"


def create_or_update_members(ometria_members_to_add: List[OmetriaMember]):
    if len(ometria_members_to_add) > 0:
        members_url = OMETRIA_BASE_URL + "record"
        headers = {
            'Authorization': OMETRIA_API_KEY,
            'Content-Type': 'application/json'
        }

        payload = [member.to_dict() for member in ometria_members_to_add]
        logger.log_info(f"Created / updated {len(ometria_members_to_add)} members.")

        return make_request('post', members_url, headers, json_data=payload)