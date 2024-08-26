# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_ckeditor import CKEditor
from google_auth_oauthlib.flow import Flow
from requests_oauthlib import OAuth2Session
from flask_mail import Mail
import stripe

db = SQLAlchemy()
login_manager = LoginManager()
ckeditor = CKEditor()
mail = Mail()
load_dotenv()


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.facebook_login'

def register_blueprints(app):
    for module_name in ('authentication', 'home', 'forms', 'billing', 'profile'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def configure_database(app):
    @app.before_first_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )

            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

            print('> Fallback to SQLite ')
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

def create_app(config):
    app = Flask(__name__)
    ckeditor.init_app(app)
    app.config.from_object(config)
    
    # Google Auth
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')

    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError("Google OAuth2 configuration values are missing!")

    client_config = {
        "web": {
            "client_id": client_id,
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri],
        }
    }

    try:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        app.config['GOOGLE_FLOW'] = Flow.from_client_config(
            client_config=client_config,
            scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
            redirect_uri=redirect_uri
        )
    except Exception as e:
        print(f"Error initializing Google Flow: {e}")
        raise
    
    # Facebook OAuth2 setup
    facebook_client_id = app.config['FACEBOOK_CLIENT_ID']
    facebook_redirect_uri = app.config['FACEBOOK_REDIRECT_URI']
    app.config['FACEBOOK_OAUTH'] = OAuth2Session(
        client_id=facebook_client_id,
        redirect_uri=facebook_redirect_uri,
        scope=['public_profile', 'email']
    )
    
    # Stripe
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    mail.init_app(app)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app
