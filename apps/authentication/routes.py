# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for, session, abort, current_app, flash
from flask_login import (current_user, login_user, logout_user)
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
from apps.authentication.util import verify_pass, generate_verification_token, send_verification_email, confirm_verification_token
import requests
from google.oauth2 import id_token
import oauthlib
import google.auth.transport.requests
from pip._vendor import cachecontrol
from requests_oauthlib import OAuth2Session
import traceback

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))

# Google Login Callback & Login
@blueprint.route('/google-login')
def google_login():
    flow = current_app.config['GOOGLE_FLOW']
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    current_app.logger.debug(f"Setting state in session: {state}")
    return redirect(authorization_url)

@blueprint.route('/callback_google')
def callback():
    try:
        current_app.logger.debug(f"Session data in callback: {session}")

        # Check if 'state' is in the session
        if "state" not in session:
            current_app.logger.error("State is missing in session!")
            return redirect(url_for('authentication_blueprint.login'))

        flow = current_app.config['GOOGLE_FLOW']
        flow.fetch_token(authorization_response=request.url)

        if not session["state"] == request.args["state"]:
            current_app.logger.error("State does not match!")
            abort(500)  # State does not match!

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=current_app.config['GOOGLE_CLIENT_ID']
        )

        email = id_info.get("email")
        user = Users.query.filter_by(email=email).first()
        if not user:
            # Create a new user
            username = email.split('@')[0]  # Use the part before @ as username
            user = Users(username=username, email=email)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('home_blueprint.index'))

    except oauthlib.oauth2.rfc6749.errors.AccessDeniedError as e:
        current_app.logger.error(f"Access denied: {e}")
        return redirect(url_for('authentication_blueprint.login'))

# Facebook Login & Callback
@blueprint.route('/facebook-login')
def facebook_login():
    facebook = current_app.config['FACEBOOK_OAUTH']
    authorization_url, state = facebook.authorization_url(
        'https://www.facebook.com/v11.0/dialog/oauth'
    )
    session['oauth_state'] = state
    return redirect(authorization_url)

@blueprint.route('/callback_facebook')
def callback_facebook():
    try:
        if 'oauth_state' not in session:
            current_app.logger.error("State is missing in session!")
            return redirect(url_for('authentication_blueprint.login'))
        
        facebook = OAuth2Session(
            client_id=current_app.config['FACEBOOK_CLIENT_ID'],
            state=session['oauth_state'],
            redirect_uri=current_app.config['FACEBOOK_REDIRECT_URI']
        )
        
        facebook.fetch_token(
            'https://graph.facebook.com/v11.0/oauth/access_token',
            client_secret=current_app.config['FACEBOOK_CLIENT_SECRET'],
            authorization_response=request.url
        )

        # Fetch user info
        user_info = facebook.get('https://graph.facebook.com/me?fields=id,name,email').json()
        email = user_info.get('email')
        if not email:
            current_app.logger.error("Email not provided by Facebook.")
            return redirect(url_for('authentication_blueprint.login'))

        user = Users.query.filter_by(email=email).first()
        if not user:
            # Create a new user
            username = email.split('@')[0]
            user = Users(username=username, email=email)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('home_blueprint.index'))

    except oauthlib.oauth2.rfc6749.errors.AccessDeniedError as e:
        current_app.logger.error(f"Access denied: {e}")
        return redirect(url_for('authentication_blueprint.login'))

# Normal Login & Registration
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()

        if user and verify_pass(password, user.password):
            if not user.is_email_verified:
                flash('Please verify your email before logging in. Check your inbox for the verification link.', 'warning')
                return render_template('accounts/login.html', form=login_form)

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        flash('Wrong username or password', 'danger')
        return render_template('accounts/login.html', form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html', form=login_form)
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:
        username = request.form['username']
        email = request.form['email']

        # Check username exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # Check if email is disposable
        debounce_url = f"https://disposable.debounce.io/?email={email}"
        try:
            response = requests.get(debounce_url)
            if response.status_code == 200:
                result = response.json()
                if result.get("disposable") == "true":
                    return render_template('accounts/register.html',
                                           msg='Please use a non-disposable email address',
                                           success=False,
                                           form=create_account_form)
        except requests.RequestException:
            current_app.logger.error("Error checking disposable email")
            # Optionally, decide how to handle API errors (e.g., allow registration or show an error)

        # Create new user
        user = Users(**request.form)
        user.is_email_verified = False
        db.session.add(user)
        db.session.commit()

        # Generate verification token and send email
        token = generate_verification_token(user.email)
        user.email_verification_token = token
        db.session.commit()
        
        try:
            current_app.logger.info(f"Attempting to send verification email to {user.email}")
            send_verification_email(user.email, token)
            current_app.logger.info(f"Verification email sent successfully to {user.email}")
            flash('A verification email has been sent to your email address. Please check your inbox.', 'success')
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('Registration successful, but we encountered an error sending the verification email. Please contact support.', 'warning')

        return render_template('accounts/register.html',
                               msg='User created successfully. Please check your email to verify your account.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)

@blueprint.route('/verify-email/<token>')
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('authentication_blueprint.login'))
    
    user = Users.query.filter_by(email=email).first()
    if user:
        if user.is_email_verified:
            flash('Email already verified. Please login.', 'info')
        else:
            user.is_email_verified = True
            user.email_verification_token = None
            db.session.commit()
            flash('Email verified successfully. You can now login.', 'success')
    else:
        flash('User not found', 'danger')
    
    return redirect(url_for('authentication_blueprint.login'))

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))

# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
