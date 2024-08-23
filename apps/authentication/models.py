# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from datetime import datetime
from apps import db, login_manager
from apps.authentication.util import hash_pass

class Users(db.Model, UserMixin):

    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(150))
    password = db.Column(db.LargeBinary)
    role = db.Column(db.String(20), nullable=False, default='user')
    subscription_type = db.Column(db.Integer, nullable=False, default=0)
    number_of_proposals = db.Column(db.Integer, nullable=False, default=0)
    free_plan_used = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True, nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)
    
    def reset_proposals(self):
        if self.subscription_type == 2:  # $20 Plan
            self.number_of_proposals += 5
        elif self.subscription_type == 3:  # $50 Plan
            self.number_of_proposals += 10
        elif self.subscription_type == 1:  # Free Plan
            # if not self.proposals_reset_date:  # Only allocate proposals once
            self.number_of_proposals += 2

        # # For paid plans, set the next reset date
        # if self.subscription_type in [2, 3]:
        #     self.proposals_reset_date = datetime.now() + relativedelta(months=1)

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None

class UsedSessionId(db.Model):
    __tablename__ = 'UsedSessionId'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True)
    
    def __repr__(self):
        return str(self.username)