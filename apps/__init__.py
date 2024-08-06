# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import pathlib
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_ckeditor import CKEditor
from google_auth_oauthlib.flow import Flow
from requests_oauthlib import OAuth2Session

db = SQLAlchemy()
login_manager = LoginManager()
ckeditor = CKEditor()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.facebook_login'  # Set the login view

def register_blueprints(app):
    for module_name in ('authentication', 'home', 'forms'):
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
    
    # Google OAuth2 configuration
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # to allow Http traffic for local dev
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
    app.config['GOOGLE_FLOW'] = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="http://localhost:5000/callback_google"
    )
    
    # Facebook OAuth2 setup
    facebook_client_id = app.config['FACEBOOK_CLIENT_ID']
    facebook_redirect_uri = app.config['FACEBOOK_REDIRECT_URI']
    app.config['FACEBOOK_OAUTH'] = OAuth2Session(
        client_id=facebook_client_id,
        redirect_uri=facebook_redirect_uri,
        scope=['public_profile', 'email']
    )
    
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app
