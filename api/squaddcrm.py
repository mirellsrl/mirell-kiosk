import os
from dotenv import load_dotenv
import requests
from typing import List, Optional
from datetime import datetime

# Load environment variables
load_dotenv()

def createSquaddCRMContact(
    name: str,
    surname: str,
    wedding: Optional[bool] = False, # if you want to update contacts in the mirell cerimonie
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    birthdate: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> dict:
    
    shop_token = os.getenv('SQUADDCRM_API_KEY')
    wedding_token = os.getenv('SQUADDCRM_API_KEY_WEDDING')

    if not shop_token:
        raise ValueError("Missing credentials: SQUADDCRM_API_KEY must be provided")
    
    if not wedding_token:
        raise ValueError("Missing credentials: SQUADDCRM_API_KEY_WEDDING must be provided")
    
    url = "https://services.leadconnectorhq.com/contacts/upsert"

    if wedding:
        location_id = "Xj2eg4ipxYYy2FjoezIW" # Mirell wedding
        token = wedding_token
    else:
        location_id = "PLiy26xI6HF7txzhrIOJ" # Mirell shop squadd
        token = shop_token

    headers = {
        "Authorization": "Bearer " + token,
        "Version": "2021-07-28",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
    "locationId": location_id,
    "firstName": name,
    "lastName": surname,
    "name" : name + " " + surname,
    "timezone": "Europe/Rome",
    "source": "Mirell Kiosk",
    }

    if phone_number:
        payload["phone"] = phone_number
    
    if email:
        payload["email"] = email

    if birthdate:
        payload["dateOfBirth"] = birthdate
        # payload["birthMonth"] = datetime.strptime(birthdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%m")
        # payload["birthDay"] = datetime.strptime(birthdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d")

    if tags is None:
        tags = ["negozio fisico"]

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        contactId = response.json()["contact"]["id"]
        
        updateTagUrl = f"https://services.leadconnectorhq.com/contacts/{contactId}/tags"

        updateTagPayload = {
            "tags": tags
        }

        response = requests.post(updateTagUrl, json=updateTagPayload, headers=headers)

        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create contact in SquaddCRM: {str(e)}")
