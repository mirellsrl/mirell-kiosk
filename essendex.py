import os
from dotenv import load_dotenv
import requests
from typing import List, Optional

# Load environment variables
load_dotenv()

def createMobytContact(
    name: str,
    surname: str, 
    phone_number: str,
    group_ids: Optional[List[str]] = None
) -> dict:
    """
    Create a contact using Essendex API
    """
    url = "https://app.esendex.it/API/v1.0/REST/contact"

    if group_ids is None:
        group_ids = ["xHyUB5MBROIErT27pLaF"] # Default group of Mirell kiosk

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
        "message_type": "N",
        "message": message,
        "recipient": recipients,
        "sender": "MIRELL",
        "returnCredits": True
    }

    headers = {
        "Content-Type": "application/json",
        "user_key": user_key,
        "Access_token": access_token,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            print(f"Error response: {e.response.text}")
        raise Exception(f"Failed to send SMS: {str(e)}")

def confirm_subscription(name: str, phone_number: str) -> dict:
    """
    Confirm subscription to Mirell Kiosk
    """
    # Send a confirmation SMS
    message = f"Ciao {name}, grazie per esserti iscritta a Mirell! Passa a trovarci sui nostri social: https://linktr.ee/mirellsrl"
    response = send_sms(message, [phone_number])
    return response