# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.profile import blueprint
from flask import flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from apps.profile.forms import ChangePasswordForm
from apps import db
from apps.authentication.util import hash_pass

@blueprint.route('/profile')
@login_required
def profile():
    return render_template('profile/profile.html')

@blueprint.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        new_password = form.new_password.data
        current_user.password = hash_pass(new_password)  # Use hash_pass directly
        db.session.commit()
        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('profile_blueprint.profile'))

    return render_template('profile/change_password.html', form=form)