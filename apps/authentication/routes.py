# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for, session, abort, current_app
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
from apps.authentication.util import verify_pass
import requests
from google.oauth2 import id_token
import google.auth.transport.requests
from pip._vendor import cachecontrol
from requests_oauthlib import OAuth2Session

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))

# Google Login
@blueprint.route('/google-login')
def google_login():
    flow = current_app.config['GOOGLE_FLOW']
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    current_app.logger.debug(f"Setting state in session: {state}")
    return redirect(authorization_url)

@blueprint.route('/callback_google')
def callback():
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

# Facebook
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

# Normal Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
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

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()

        return render_template('accounts/register.html',
                               msg='User created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)
    
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
