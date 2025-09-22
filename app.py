# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, make_response, render_template_string
from essendex import createMobytContact, confirm_subscription
from squaddcrm import createSquaddCRMContact
from brevo import createBrevoContact
from datetime import datetime
from dotenv import load_dotenv
import re, os, logging, sys, json, random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
    )

# Load environment variables at startup
load_dotenv()

# Verify environment variables
if not os.getenv('USER_KEY') or not os.getenv('ACCESS_TOKEN'):
    raise ValueError("Missing required environment variables. Check your .env file")

app = Flask(__name__)
app.secret_key = "reO0jZmUgFCO0g3fy0wAbsYyXHN3OsJD"  # Required for session management

# Configure session for PWA compatibility
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Allow JavaScript access for PWA
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Better PWA compatibility

# Add ping route
@app.route('/healthz')
def health():
    return "OK"

# Add a method to wake up the app
@app.route('/wakeup')
def wakeup():
    logging.info("System is woken up")
    return "I'm awake!"

# Add a service worker route
@app.route('/static/js/sw.js')
def sw():
    response = make_response(
        send_from_directory('static/js', 'sw.js')
    )
    response.headers['Content-Type'] = 'application/javascript'
    return response

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

def select_prize():
    """Select a prize based on probability weights from the JSON file"""
    try:
        with open('fiera_prizes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        prizes = data['prizes']
        # Create a weighted list based on probability
        weighted_prizes = []
        for prize in prizes:
            # Add each prize to the list based on its probability
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

@app.route('/', methods=['GET'])
def start():
    session.clear()
    return redirect(url_for('step1'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static/images'),
        'favicon.png', 
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/step1', methods=['GET', 'POST'])
def step1():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        if not name:           
            flash("Il nome è obbligatorio.", "error")
            return render_template('step1.html')
        if not surname:
            flash("Il cognome è obbligatorio.", "error")
            return render_template('step1.html')
        session['name'] = name
        session['surname'] = surname
        return redirect(url_for('step2'))
    return render_template('step1.html')

@app.route('/step2', methods=['GET', 'POST'])
def step2():
    if 'name' not in session:
        return redirect(url_for('step1'))
    if request.method == 'POST':
        email = request.form['email']
        if email and not is_valid_email(email):
            flash("L'email inserita non è valida.", "error")
            return render_template('step2.html', name=session['name'])
        session['email'] = email
        return redirect(url_for('step3'))
    return render_template('step2.html', name=session['name'])

@app.route('/step3', methods=['GET', 'POST'])
def step3():
    if 'name' not in session:
        return redirect(url_for('step1'))
    if request.method == 'POST':
        session['phone'] = request.form.get('phone', '')
        return redirect(url_for('step4'))
    return render_template('step3.html')

@app.route('/step4', methods=['GET', 'POST'])
def step4():
    if 'name' not in session:
        return redirect(url_for('step1'))
    if request.method == 'POST':
        session['birthdate'] = request.form.get('birthdate', '')
        return redirect(url_for('step5'))
    return render_template('step4.html')

@app.route('/step5', methods=['GET', 'POST'])
def step5():
    if 'name' not in session:
        return redirect(url_for('step1'))
    if not session.get('email') and not session.get('phone'):
        flash("Non hai inserito né un numero di telefono né un'email. Torna indietro e aggiungi almeno uno dei due per ricevere le nostre fantastiche sorprese! 😊.", "error")
        return redirect(url_for('step2'))
    if request.method == 'POST':
        if 'privacy_accept' in request.form:
            try:
                session['sms_marketing_accept'] = 'sms_marketing_accept' in request.form
                session['email_marketing_accept'] = 'email_marketing_accept' in request.form
                return redirect(url_for('thank_you'))
            except Exception as e:
                return render_template('error.html', error=str(e))
    return render_template('step5.html')

@app.route('/thank-you')
def thank_you():
    name = session['name']
    surname = session['surname']
    email = session.get('email')
    phone = session.get('phone')
    birthdate = session.get('birthdate')

    if birthdate:
        birthdate = datetime.strptime(birthdate, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    tags = ["negozio fisico", "da revisionare"]

    if phone and session.get('sms_marketing_accept'):
        phone = "+39" + phone
        createMobytContact(name, surname, phone, birthdate=birthdate)
        # confirm_subscription(name, phone)
        if email and session.get('email_marketing_accept'):
            # createBrevoContact(email, name, surname, birthdate, phone)
            createSquaddCRMContact(name=name, surname=surname, wedding=False, email=email, phone_number=phone, birthdate=birthdate, tags=tags)
        else:
            createSquaddCRMContact(name=name, surname=surname, wedding=False, phone_number=phone, birthdate=birthdate, tags=tags)

    logging.info(f"Contact {name} {surname} created successfully")
    return render_template('thank_you.html')

@app.route('/wedding', methods=['GET', 'POST'])
def wedding():
    # Extract parameters from the URL
    fullname = request.args.get('fullname', '')
    phone = request.args.get('phone', '')

    # make the text capitalize
    fullname = fullname.strip().title()

    # Split the fullname into name and surname
    name, surname = "", ""
    if fullname:
        parts = fullname.split(' ', 1)
        name = parts[0]
        surname = parts[1] if len(parts) > 1 else ""
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        birthdate = request.form.get('birthdate', '').strip()
        
        # Validate required fields
        if not name or not surname:
            flash("Nome e cognome sono obbligatori.", "error")
            return render_template('wedding.html', name=name, surname=surname, phone=phone, email=email, birthdate=birthdate)
            
        if not email and not phone:
            flash("Inserisci almeno un contatto (email o telefono).", "error")
            return render_template('wedding.html', name=name, surname=surname, phone=phone, email=email, birthdate=birthdate)
        
        if email and not is_valid_email(email):
            flash("L'email inserita non è valida.", "error")
            return render_template('wedding.html', name=name, surname=surname, phone=phone, email=email, birthdate=birthdate)
        
        # Since this is an internal platform, we always add the default tags
        tags = ["negozio fisico", "cliente wedding", "da revisionare"]
        
        # Process the data - create contact in Squadd
        try:
            if birthdate:
                birthdate = datetime.strptime(birthdate, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                
            if phone:
                if email:
                    createSquaddCRMContact(name=name, surname=surname, wedding=False, email=email, phone_number=phone, birthdate=birthdate, tags=tags)
                else:
                    createSquaddCRMContact(name=name, surname=surname, wedding=False, phone_number=phone, birthdate=birthdate, tags=tags)
            elif email:
                createSquaddCRMContact(name=name, surname=surname, wedding=False, email=email, birthdate=birthdate, tags=tags)
                
            logging.info(f"Wedding form submission for {name} {surname} created successfully with tags: {', '.join(tags)}")
            return render_template('newsletter_thank_you.html')
        except Exception as e:
            logging.error(f"Error creating contact: {str(e)}")
            flash("Si è verificato un errore. Riprova più tardi.", "error")
            return render_template('wedding.html', name=name, surname=surname, phone=phone, email=email, birthdate=birthdate)
    
    # For GET request, show the form with pre-populated values
    return render_template('wedding.html', name=name, surname=surname, phone=phone)

@app.route('/fiera', methods=['GET'])
def fiera():
    """Main fiera PWA route - displays the form"""
    # Check if device is authorized
    logging.info(f"Fiera route accessed. Device authorized: {session.get('device_authorized')}")
    if not session.get('device_authorized'):
        logging.info("Redirecting to auth - device not authorized")
        return redirect(url_for('fiera_auth'))
    
    session.pop('fiera_name', None)
    session.pop('fiera_surname', None)
    session.pop('fiera_phone', None)
    session.pop('fiera_client_type', None)
    session.pop('fiera_tags', None)
    return render_template('fiera.html')

@app.route('/fiera/auth', methods=['GET', 'POST'])
def fiera_auth():
    """Device authentication for fiera PWA"""
    if request.method == 'POST':
        device_key = request.form.get('device_key', '').strip()
        expected_key = os.getenv('FIERA_DEVICE_KEY')
        
        if not expected_key:
            flash("Configurazione del sistema non valida. Contatta l'amministratore.", "error")
            return render_template('fiera_auth.html')
        
        if device_key == expected_key:
            session['device_authorized'] = True
            logging.info(f"Fiera device authorized from {request.remote_addr}")
            return redirect(url_for('fiera'))
        else:
            logging.warning(f"Failed fiera auth attempt from {request.remote_addr} with key: {device_key}")
            flash("Codice dispositivo non valido.", "error")
            return render_template('fiera_auth.html')
    
    # If already authorized, redirect to fiera
    current_auth_status = session.get('device_authorized')
    logging.info(f"Auth page accessed. Current auth status: {current_auth_status}")
    if current_auth_status:
        logging.info("Already authorized, redirecting to fiera")
        return redirect(url_for('fiera'))
    
    return render_template('fiera_auth.html')

@app.route('/fiera/submit', methods=['POST'])
def fiera_submit():
    """Handle fiera form submission and create contact"""
    # Check if device is authorized
    if not session.get('device_authorized'):
        return {'success': False, 'error': 'Accesso non autorizzato'}, 403
    
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        surname = request.form.get('surname', '').strip()
        phone = request.form.get('phone', '').strip()
        client_type = request.form.get('client_type', '').strip()
        privacy_accept = 'privacy_accept' in request.form
        
        # Validate required fields
        if not name or not surname or not phone or not client_type or not privacy_accept:
            return {'success': False, 'error': 'Tutti i campi sono obbligatori'}, 400
        
        # Determine client type tag
        client_type_tags = {
            'sposa': 'fiera-sposa',
            'mamma-sposa': 'fiera-mamma-sposa',
            'mamma-sposo': 'fiera-mamma-sposo',
            'testimone': 'fiera-testimone',
            'altro': 'fiera-altro'
        }
        
        client_tag = client_type_tags.get(client_type, 'fiera-altro')
        tags = ["fiera", client_tag]
        
        # Format phone number
        if phone and not phone.startswith('+39'):
            phone = "+39" + phone
        
        # Create contact in SquaddCRM (wedding = True)
        createSquaddCRMContact(
            name=name, 
            surname=surname, 
            wedding=True, 
            phone_number=phone, 
            tags=tags
        )
        
        # Store user data in session for game
        session['fiera_name'] = name
        session['fiera_surname'] = surname
        session['fiera_phone'] = phone
        session['fiera_client_type'] = client_type
        session['fiera_tags'] = tags
        
        logging.info(f"Fiera contact {name} {surname} created successfully with tags: {', '.join(tags)}")
        return {'success': True}, 200
        
    except Exception as e:
        logging.error(f"Error creating fiera contact: {str(e)}")
        return {'success': False, 'error': 'Si è verificato un errore. Riprova più tardi.'}, 500

@app.route('/fiera/game', methods=['POST'])
def fiera_game():
    """Handle the game play and prize selection"""
    # Check if device is authorized
    if not session.get('device_authorized'):
        return {'success': False, 'error': 'Accesso non autorizzato'}, 403
    
    try:
        # Check if user has submitted form
        if 'fiera_name' not in session:
            return {'success': False, 'error': 'Devi prima compilare il modulo'}, 400
        
        # Select a prize
        prize = select_prize()
        
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
        
        logging.info(f"Fiera game completed for {name} {surname}. Prize: {prize['name']}")
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

@app.route('/fiera/reset', methods=['POST'])
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

@app.route('/fiera/logout', methods=['POST'])
def fiera_logout():
    """Logout and clear device authorization"""
    session.clear()
    return {'success': True}, 200

if __name__ == '__main__':
    logging.info("Starting the app")
    load_dotenv()
    app.run(debug=True)