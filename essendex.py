import os
from dotenv import load_dotenv
import requests
from typing import List, Optional

# Load environment variables
load_dotenv()

def create_contact(
    name: str,
    surname: str, 
    phone_number: str,
    email: Optional[str] = None,
    gender: Optional[str] = None,
    fax: Optional[str] = None,
    zip_code: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    birthdate: Optional[str] = None,
    group_ids: Optional[List[str]] = None
) -> dict:
    """
    Create a contact using Essendex API
    """
    url = "https://app.esendex.it/API/v1.0/REST/contact"

    # Use provided credentials or fall back to env variables
    user_key = user_key or os.getenv('USER_KEY')
    access_token = access_token or os.getenv('ACCESS_TOKEN')

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
        "email": email,
        "gender": gender,
        "fax": fax,
        "zip": zip_code,
        "address": address,
        "city": city,
        "province": province,
        "birthdate": birthdate,
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