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
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    birthdate: Optional[str] = None,
) -> dict:
    
    token = os.getenv('SQUADDCRM_API_KEY')

    if not token:
        raise ValueError("Missing credentials: SQUADDCRM_API_KEY must be provided")
    
    url = "https://services.leadconnectorhq.com/contacts/upsert"

    headers = {
        "Authorization": "Bearer " + os.getenv('SQUADDCRM_API_KEY'),
        "Version": "2021-07-28",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
    "locationId": "PLiy26xI6HF7txzhrIOJ",
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

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        contactId = response.json()["contact"]["id"]
        
        updateTagUrl = f"https://services.leadconnectorhq.com/contacts/{contactId}/tags"

        updateTagPayload = {
            "tags": ["negozio fisico"]
        }

        response = requests.post(updateTagUrl, json=updateTagPayload, headers=headers)

        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create contact in SquaddCRM: {str(e)}")
    
