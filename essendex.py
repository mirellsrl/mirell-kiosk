import os
from dotenv import load_dotenv
import requests
from typing import List, Optional
import json

# Load environment variables
load_dotenv()

def create_contact(
    name: str,
    surname: str, 
    phone_number: str,
    group_ids: Optional[List[str]] = None
) -> dict:
    """
    Create a contact using Essendex API
    """
    url = "https://app.esendex.it/API/v1.0/REST/contact"

    # Use provided credentials or fall back to env variables
    user_key = os.getenv('USER_KEY')
    access_token = os.getenv('ACCESS_TOKEN')

    if not user_key or not access_token:
        raise ValueError("Missing credentials: USER_KEY and ACCESS_TOKEN must be provided")

    
    headers = {
        "Content-Type": "application/json",
        "user_key": user_key,
        "Access_token": access_token
    }
    
    payload = {
        "name": name,
        "surname": surname,
        "phoneNumber": phone_number,
        "groupIds": group_ids or []
    }
    
    # Remove None values from payload
    payload = {k: v for k, v in payload.items() if v is not None}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create contact: {str(e)}")

def send_sms(
    message: str,
    recipients: List[str],
) -> dict:
    """
    Send an SMS using Essendex API
    """
    url = "https://app.esendex.it/API/v1.0/REST/sms"

    # Use provided credentials or fall back to env variables
    user_key = os.getenv('USER_KEY')
    access_token = os.getenv('ACCESS_TOKEN')

    if not user_key or not access_token:
        raise ValueError("Missing credentials: USER_KEY and ACCESS_TOKEN must be provided")
    
    payload = {
        "message_type": "LL",
        "message": message,
        "recipients": recipients,
        "returnCredits": True
    }

    payload_json = json.dumps(payload)

    print(payload_json)

    headers = {
        "Content-Type": "application/json",
        "user_key": user_key,
        "Access_token": access_token,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload_json)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to send SMS: {str(e)}")
    

def greet(name: str, phone_number: str) -> dict:
    """
    Greet a contact by sending an SMS
    """
    message = f"Hello {name}, this is a test message from Mirell"
    return send_sms(message, [phone_number])
   