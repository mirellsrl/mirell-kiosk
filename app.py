# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from essendex import createMobytContact
from brevo import createBrevoContact
from datetime import datetime
from dotenv import load_dotenv
import re, os, logging, sys

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

# Add ping route
@app.route('/healthz')
def health():
    return "OK"

# Add a method to wake up the app
@app.route('/wakeup')
def wakeup():
    logging.info("System is woken up")
    return "I'm awake!"

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

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
        if not email:
            flash("L'email è obbligatoria.", "error")
            return render_template('step2.html', name=session['name'])
        if not is_valid_email(email):
            flash("L'email inserita non è valida.", "error")
            return render_template('step2.html', name=session['name'])
        session['email'] = email
        return redirect(url_for('step3'))
    return render_template('step2.html', name=session['name'])

@app.route('/step3', methods=['GET', 'POST'])
def step3():
    if 'email' not in session:
        return redirect(url_for('step2'))
    if request.method == 'POST':
        session['phone'] = request.form.get('phone', '')
        return redirect(url_for('step4'))
    return render_template('step3.html')

@app.route('/step4', methods=['GET', 'POST'])
def step4():
    if 'email' not in session:
        return redirect(url_for('step2'))
    if request.method == 'POST':
        session['birthdate'] = request.form.get('birthdate', '')
        return redirect(url_for('step5'))
    return render_template('step4.html')

@app.route('/step5', methods=['GET', 'POST'])
def step5():
    if request.method == 'POST':
        if 'privacy_accept' in request.form:
            try:
                return redirect(url_for('thank_you'))
            except Exception as e:
                return render_template('error.html', error=str(e))
    return render_template('step5.html')

@app.route('/thank-you')
def thank_you():
    name = session['name']
    surname = session['surname']
    email = session['email']
    phone = session['phone']
    birthdate = session['birthdate']

    if birthdate:
        birthdate = datetime.strptime(birthdate, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    if phone:
        phone = "+39" + phone
        createMobytContact(name, surname, phone)

    createBrevoContact(email, name, surname, birthdate, phone)
    logging.info(f"Contact {name} {surname} created successfully")
    return render_template('thank_you.html')

if __name__ == '__main__':
    logging.info("Starting the app")
    load_dotenv()
    app.run(debug=True)