from functools import wraps
from flask import render_template, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return render_template('home/page-403.html'), 403
        return f(*args, **kwargs)
    return decorated_function

def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.subscription_type == 0:
            return render_template('home/page-403.html'), 403
        return f(*args, **kwargs)
    return decorated_function

def proposal_charges_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.number_of_proposals == 0:
            return redirect(url_for('billing_blueprint.proposal_charges_empty'))
        return f(*args, **kwargs)
    return decorated_function