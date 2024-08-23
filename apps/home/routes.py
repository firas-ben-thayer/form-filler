# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, redirect, request, url_for
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

@blueprint.route('/index')
@login_required
def index():
    if current_user.role == 'admin':
        return render_template('home/index.html', segment='index')
    elif current_user.subscription_type == 0:
        return redirect(url_for('billing_blueprint.billing'))
    else:
        return redirect(url_for('forms_blueprint.view_forms'))


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
