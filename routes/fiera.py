"""Fiera PWA routes and event-based configuration"""
from flask import render_template, request, redirect, url_for, session, Blueprint
from api import createSquaddCRMContact
import logging
import json
import random
import os

fiera_bp = Blueprint('fiera', __name__, url_prefix='/fiera')

def load_events_config():
    """Load events configuration from JSON file"""
    try:
        with open('events_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("events_config.json not found. Please create the configuration file.")
        return {'events': {}}
    except json.JSONDecodeError:
        logging.error("Invalid JSON in events_config.json")
        return {'events': {}}

def get_event_by_password(password):
    """Get event configuration by password"""
    config = load_events_config()
    password_lower = password.lower().strip()
    logging.debug(f"Looking for password: '{password_lower}' in available events")
    for event_key, event_config in config.get('events', {}).items():
        stored_password = event_config.get('password', '').lower().strip()
        logging.debug(f"  Checking event '{event_key}': stored='{stored_password}'")
        if stored_password == password_lower:
            logging.info(f"Password matched for event: {event_key}")
            return event_key, event_config
    logging.warning(f"No event found for password: {password_lower}")
    return None, None

def select_prize(event_key):
    """Select a prize based on probability weights for specific event"""
    try:
        config = load_events_config()
        event_config = config.get('events', {}).get(event_key, {})
        
        # Check if event has custom prizes, otherwise use default
        if 'prizes' in event_config:
            prizes = event_config['prizes']
        else:
            # Fall back to default prizes
            with open('fiera_prizes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                prizes = data['prizes']
        
        # Create a weighted list based on probability
        weighted_prizes = []
        for prize in prizes:
            weighted_prizes.extend([prize] * prize['probability'])
        
        # Select a random prize
        selected_prize = random.choice(weighted_prizes)
        return selected_prize
    except Exception as e:
        logging.error(f"Error selecting prize: {str(e)}")
        # Return a default prize if there's an error
        return {
            "name": "Accessorio Gratuito",
            "description": "Scegli un accessorio gratuito dalla nostra collezione",
            "probability": 25,
            "tag": "accessorio-gratuito"
        }

@fiera_bp.route('/', methods=['GET'])
def fiera():
    """Main fiera PWA route - displays the form"""
    logging.info(f"Fiera route accessed. Device authorized: {session.get('device_authorized')}")
    if not session.get('device_authorized'):
        logging.info("Redirecting to auth - device not authorized")
        return redirect(url_for('fiera.fiera_auth'))
    
    # Clear any previous game session data
    session.pop('fiera_name', None)
    session.pop('fiera_surname', None)
    session.pop('fiera_phone', None)
    session.pop('fiera_client_type', None)
    session.pop('fiera_tags', None)
    
    event_key = session.get('event_key', '')
    config = load_events_config()
    event_config = config.get('events', {}).get(event_key, {})
    
    return render_template('fiera.html', 
                         welcome_message=event_config.get('welcome_message', 'Benvenuto alla Fiera!'))

@fiera_bp.route('/auth', methods=['GET', 'POST'])
def fiera_auth():
    """Device authentication for fiera PWA using event password"""
    if request.method == 'POST':
        device_password = request.form.get('device_key', '').strip()
        
        # Get event by password
        event_key, event_config = get_event_by_password(device_password)
        
        if event_key and event_config:
            session['device_authorized'] = True
            session['event_key'] = event_key
            logging.info(f"Fiera device authorized for event '{event_key}' from {request.remote_addr}")
            return redirect(url_for('fiera.fiera'))
        else:
            logging.warning(f"Failed fiera auth attempt from {request.remote_addr} with key: {device_password}")
            # Don't reveal if password is wrong - just generic message
            return render_template('fiera_auth.html', error="Codice dispositivo non valido.")
    
    # If already authorized, redirect to fiera
    if session.get('device_authorized'):
        logging.info("Already authorized, redirecting to fiera")
        return redirect(url_for('fiera.fiera'))
    
    return render_template('fiera_auth.html', error="")

@fiera_bp.route('/submit', methods=['POST'])
def fiera_submit():
    """Handle fiera form submission and create contact"""
    # Check if device is authorized
    if not session.get('device_authorized'):
        return {'success': False, 'error': 'Accesso non autorizzato'}, 403
    
    try:
        event_key = session.get('event_key')
        config = load_events_config()
        event_config = config.get('events', {}).get(event_key, {})
        tag_prefix = event_config.get('tag_prefix', 'fiera')
        
        # Get form data
        name = request.form.get('name', '').strip()
        surname = request.form.get('surname', '').strip()
        phone = request.form.get('phone', '').strip()
        client_type = request.form.get('client_type', '').strip()
        privacy_accept = 'privacy_accept' in request.form
        
        # Validate required fields
        if not name or not surname or not phone or not client_type or not privacy_accept:
            return {'success': False, 'error': 'Tutti i campi sono obbligatori'}, 400
        
        # Determine client type tag using configured tag prefix
        client_type_tags = {
            'sposa': f'{tag_prefix}-sposa',
            'mamma-sposa': f'{tag_prefix}-mamma-sposa',
            'mamma-sposo': f'{tag_prefix}-mamma-sposo',
            'testimone': f'{tag_prefix}-testimone',
            'altro': f'{tag_prefix}-altro'
        }
        
        client_tag = client_type_tags.get(client_type, f'{tag_prefix}-altro')
        
        # Create tags: event name, client type, and combined
        tags = [
            tag_prefix,                    # Event name (e.g., "fiera-2025")
            client_type,                   # Client type (e.g., "sposa")
            client_tag                     # Combined (e.g., "fiera-2025-sposa")
        ]
        
        # Format phone number
        if phone and not phone.startswith('+39'):
            phone = "+39" + phone
        
        # Create contact in SquaddCRM (wedding = True)
        result = createSquaddCRMContact(
            name=name, 
            surname=surname, 
            wedding=True, 
            phone_number=phone, 
            tags=tags
        )
        
        # Check if user has already played
        user_tags = result.get('tags', [])
        if 'partita-effettuata' in user_tags:
            logging.info(f"User {name} {surname} has already played the game")
            return {
                'success': False, 
                'error': 'Hai già giocato! Ogni persona può giocare una sola volta.',
                'already_played': True
            }, 400
        
        # Store user data in session for game
        session['fiera_name'] = name
        session['fiera_surname'] = surname
        session['fiera_phone'] = phone
        session['fiera_client_type'] = client_type
        session['fiera_tags'] = tags
        
        logging.info(f"Fiera contact {name} {surname} created successfully for event '{event_key}' with tags: {', '.join(tags)}")
        return {'success': True}, 200
        
    except Exception as e:
        logging.error(f"Error creating fiera contact: {str(e)}")
        return {'success': False, 'error': 'Si è verificato un errore. Riprova più tardi.'}, 500

@fiera_bp.route('/game', methods=['POST'])
def fiera_game():
    """Handle the game play and prize selection"""
    # Check if device is authorized
    if not session.get('device_authorized'):
        return {'success': False, 'error': 'Accesso non autorizzato'}, 403
    
    try:
        # Check if user has submitted form
        if 'fiera_name' not in session:
            return {'success': False, 'error': 'Devi prima compilare il modulo'}, 400
        
        event_key = session.get('event_key')
        
        # Select a prize for this event
        prize = select_prize(event_key)
        
        # Update contact with game tags
        name = session['fiera_name']
        surname = session['fiera_surname']
        phone = session['fiera_phone']
        existing_tags = session['fiera_tags']
        
        # Add game completion and prize tags
        updated_tags = existing_tags + ["partita-effettuata", prize['tag']]
        
        # Update contact in SquaddCRM
        createSquaddCRMContact(
            name=name, 
            surname=surname, 
            wedding=True, 
            phone_number=phone, 
            tags=updated_tags
        )
        
        logging.info(f"Fiera game completed for {name} {surname} in event '{event_key}'. Prize: {prize['name']}")
        return {
            'success': True, 
            'prize': {
                'name': prize['name'],
                'description': prize['description']
            }
        }, 200
        
    except Exception as e:
        logging.error(f"Error in fiera game: {str(e)}")
        return {'success': False, 'error': 'Si è verificato un errore durante il gioco'}, 500

@fiera_bp.route('/reset', methods=['POST'])
def fiera_reset():
    """Reset the game session"""
    # Check if device is authorized  
    if not session.get('device_authorized'):
        return {'success': False, 'error': 'Accesso non autorizzato'}, 403
        
    # Clear only game-related session data, keep device authorization
    session.pop('fiera_name', None)
    session.pop('fiera_surname', None)
    session.pop('fiera_phone', None)
    session.pop('fiera_client_type', None)
    session.pop('fiera_tags', None)
    return {'success': True}, 200

@fiera_bp.route('/logout', methods=['POST'])
def fiera_logout():
    """Logout and clear device authorization"""
    session.clear()
    return {'success': True}, 200
