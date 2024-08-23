from functools import wraps
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from apps.forms.models import Forms

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
        form_id = kwargs.get('form_id')
        form = Forms.query.get(form_id)
        if form:
            # If the user has no proposals and the form's download limit is reached, redirect to billing
            if (form.number_of_downloads >= 3 and current_user.number_of_proposals == 0) or (form.number_of_downloads == 0 and current_user.number_of_proposals == 0):
                return redirect(url_for('billing_blueprint.proposal_charges_empty'))
        
        return f(*args, **kwargs)
    return decorated_function

def prevent_step_one_if_editing(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        form_id = kwargs.get('form_id') or request.args.get('form_id')
        step = kwargs.get('step')
        if form_id:
            form = Forms.query.get(form_id)
            if form and step == 1 and form.number_of_downloads != 0:
                flash('You cannot go back to Step 1 while editing a form.', 'warning')
                return redirect(url_for('forms_blueprint.submit_form', step=2, form_id=form_id))
        return f(*args, **kwargs)
    return decorated_function