import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv
import os

load_dotenv()

def createBrevoContact(
    email: str,
    name: str,
    surname: str,
    bitrhdate: str = None,
    phone_number: str = None,
    list_ids: list[str] = None,

) -> dict:
    """
    Create a contact using Sendinblue API
    """

    if list_ids is None:
        list_ids = [29] # Set default list of Mirell kiosk

    api_key = os.getenv('BREVO_API_KEY')

    if not api_key:
        raise ValueError("Missing credentials: BREVO_API_KEY must be provided")

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    attributes = {
        "NOME": name,
        "COGNOME": surname
    }

    if bitrhdate is not None:
        attributes["BIRTHDAY"] = bitrhdate

    if phone_number is not None:
        attributes["SMS"] = phone_number

    create_contact = sib_api_v3_sdk.CreateContact(email=email, list_ids=list_ids, attributes=attributes)

    try:
        api_response = api_instance.create_contact(create_contact)
        return api_response
    except ApiException as e:
        print("Exception when calling Brevo ContactsApi->create_contact: %s\n" % e)