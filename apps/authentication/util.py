# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import hashlib
import binascii
from flask_mail import Message
from apps import mail
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for

# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/


def hash_pass(password):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""

    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-verification-salt',
            max_age=expiration
        )
    except:
        return False
    return email

def send_verification_email(user_email, token):
    verify_url = url_for('authentication_blueprint.verify_email', token=token, _external=True)
    html = f'<p>Please click the link to verify your email: <a href="{verify_url}">{verify_url}</a></p>'
    
    try:
        msg = Message('Verify Your Email', recipients=[user_email], html=html)
        current_app.logger.info(f"Attempting to send email to {user_email}")
        current_app.logger.info(f"MAIL_USERNAME: {current_app.config['MAIL_USERNAME']}")
        current_app.logger.info(f"MAIL_DEFAULT_SENDER: {current_app.config['MAIL_DEFAULT_SENDER']}")
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {user_email}")
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        current_app.logger.error(f"Error details: {e.__class__.__name__}: {str(e)}")
        raise