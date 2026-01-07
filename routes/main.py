"""Main routes for the kiosk application"""
from flask import render_template, request, redirect, url_for, session, flash
from api import createMobytContact, createSquaddCRMContact
from datetime import datetime
import re
import logging

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

def register_main_routes(app):
    """Register main application routes"""

    @app.route('/', methods=['GET'])
    def start():
        session.clear()
        return redirect(url_for('step1'))

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
        
        tags = ["negozio fisico", "da revisionare", "top"]

        if phone and session.get('sms_marketing_accept'):
            phone = "+39" + phone
            createMobytContact(name, surname, phone, birthdate=birthdate)
            if email and session.get('email_marketing_accept'):
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
            tags = ["negozio fisico", "cliente wedding", "da revisionare", "top"]
            
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
