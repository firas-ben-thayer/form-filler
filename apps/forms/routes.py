# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for, flash, session, send_file
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from apps import db, login_manager
from apps.forms import blueprint
from apps.forms.forms import CreateForm, TableForm
from apps.forms.models import Forms, TableEntry
from flask_login import current_user, login_required


@blueprint.route('/view_forms')
@login_required
def view_forms():
    forms = Forms.query.filter_by(user_id=current_user.id).all()
    return render_template('forms/view_forms.html', forms=forms)

@blueprint.route('/new_form')
@login_required
def new_form():
    session.pop('form_data', None)
    return redirect(url_for('forms_blueprint.submit_form', step=1))

@blueprint.route('/edit_form/<int:form_id>/<int:step>', methods=['GET', 'POST'])
@login_required
def edit_form(form_id, step):
    return redirect(url_for('forms_blueprint.submit_form', step=1, form_id = form_id))

@blueprint.route('/submit_form/<int:step>', methods=['GET', 'POST'])
@login_required
def submit_form(step):
    form = CreateForm()
    table_form = TableForm()

    total_steps = 3

    if 'form_data' not in session:
        session['form_data'] = {}

    if step < 1 or step > total_steps:
        flash('Invalid step. Redirecting to the first step.', 'warning')
        return redirect(url_for('forms_blueprint.submit_form', step=1))
    
    # Check if a form_id is provided
    form_id = request.args.get('form_id')
    if form_id:
        existing_form = Forms.query.get(form_id)
        if existing_form and existing_form.user_id == current_user.id:
            form_data = existing_form.__dict__.copy()
            # Remove any non-serializable attributes
            form_data.pop('_sa_instance_state', None)
            session['form_data'] = form_data
            session.modified = True
            
    if request.method == 'POST':
        if step == 1:
            if form.validate_on_submit():
                form_data = {field.name: field.data for field in form if field.name not in ('csrf_token', 'submit')}
                session['form_data'].update(form_data)
                session.modified = True

                # Save the form data to the database
                form_data = session['form_data'].copy()
                form_data.pop('user_id', None)  # Remove user_id if it exists to not create errors
                new_form = Forms(user_id=current_user.id, **form_data)
                if not new_form.id:
                    db.session.add(new_form)
                    db.session.commit()

                # Save the form ID in the session
                session['form_data']['id'] = new_form.id
                session.modified = True

                return redirect(url_for('forms_blueprint.submit_form', step=2))
            
        elif step == 2:
            if table_form.validate_on_submit():
                new_entry = TableEntry(
                    form_id=session['form_data']['id'],
                    item_no=table_form.item_no.data,
                    description=table_form.description.data,
                    quantity=table_form.quantity.data,
                    unit=table_form.unit.data,
                    unit_price=table_form.unit_price.data
                )
                db.session.add(new_entry)
                db.session.commit()
                flash('Table entry added successfully.', 'success')
                return redirect(url_for('forms_blueprint.submit_form', step=2))
            else:
                return redirect(url_for('forms_blueprint.submit_form', step=3))

        elif step == 3:
            form_id = session['form_data']['id']
            existing_form = Forms.query.get(form_id)
            if existing_form and existing_form.user_id == current_user.id:
                for field_name, field_value in session['form_data'].items():
                    if hasattr(existing_form, field_name):
                        setattr(existing_form, field_name, field_value)
                db.session.commit()
            else:
                flash('Error: Form not found or you do not have permission to edit it.', 'error')
                return redirect(url_for('forms_blueprint.submit_form', step=1))

            document = Document()
            heading = document.add_paragraph()
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = heading.add_run('Solicitation Number and Title')
            run.font.name = 'Arial'
            run.bold = True
            run.font.size = Pt(18)

            document.add_paragraph("\n")

            solicitation_number = document.add_paragraph()
            solicitation_number.alignment = WD_ALIGN_PARAGRAPH.CENTER
            solicitation_number_run = solicitation_number.add_run(str(session['form_data'].get('solicitation_number')))
            solicitation_number_run.bold = True
            solicitation_number_run.font.name = 'Arial'
            solicitation_number_run.font.size = Pt(16)

            document.add_paragraph("\n\n")

            title = document.add_paragraph()
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title_run = title.add_run(str(session['form_data'].get('title')))
            title_run.bold = True
            title_run.font.name = 'Arial'
            title_run.font.size = Pt(16)

            def add_bold_paragraph(text):
                paragraph = document.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = paragraph.add_run(text)
                run.bold = True
                run.font.name = 'Arial'
                run.font.size = Pt(11)
                return paragraph

            def add_normal_text(paragraph, text):
                run = paragraph.add_run(text)
                run.font.name = 'Arial'
                run.font.size = Pt(11)

            document.add_paragraph("\n\n\n\n\n\n\n\n\n")

            paragraph = add_bold_paragraph("Unique Entity ID: ")
            add_normal_text(paragraph, str(session['form_data'].get('unique_entity_id')))

            paragraph = add_bold_paragraph("Phone Number: ")
            add_normal_text(paragraph, str(session['form_data'].get('phone_number')))

            paragraph = add_bold_paragraph("POC Email: ")
            add_normal_text(paragraph, str(session['form_data'].get('poc_email')))

            paragraph = add_bold_paragraph("CAGE Code: ")
            add_normal_text(paragraph, str(session['form_data'].get('cage_code')))

            paragraph = add_bold_paragraph("EIN/GST-HST Number: ")
            add_normal_text(paragraph, str(session['form_data'].get('ein_gst_hst_number')))

            paragraph = add_bold_paragraph("POC: ")
            add_normal_text(paragraph, str(session['form_data'].get('poc')))

            document.add_page_break()

            table_entries = TableEntry.query.filter_by(form_id=form_id).all()

            if table_entries:
                table = document.add_table(rows=len(table_entries) + 1, cols=6)
                table.style = 'Table Grid'
                header = table.rows[0].cells
                header[0].text = 'Item No'
                header[1].text = 'Description'
                header[2].text = 'Quantity'
                header[3].text = 'Unit'
                header[4].text = 'Unit Price'
                header[5].text = 'Ext Price'

                for i, entry in enumerate(table_entries, start=1):
                    row = table.rows[i].cells
                    row[0].text = str(entry.item_no)
                    row[1].text = entry.description
                    row[2].text = str(entry.quantity)
                    row[3].text = entry.unit
                    row[4].text = f"${entry.unit_price:.2f}"
                    row[5].text = f"${entry.quantity * entry.unit_price:.2f}"
            else:
                document.add_paragraph("No table entries found.")

            byte_io = BytesIO()
            document.save(byte_io)
            byte_io.seek(0)

            session.pop('form_data', None)

            flash('Form submitted successfully! Your document is ready for download.', 'success')
            return send_file(byte_io, as_attachment=True, download_name='Completed_Proposal_Notice.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    if step == 1:
        for field in form:
            if field.name in session.get('form_data', {}):
                field.data = session['form_data'][field.name]

    table_entries = []
    if step == 2:
        form_id = session['form_data'].get('id')
        if form_id:
            table_entries = TableEntry.query.filter_by(form_id=form_id).all()
        for field in table_form:
            if field.name in session.get('form_data', {}):
                field.data = session['form_data'][field.name]

    return render_template('forms/submit_form.html', form=form, table_form=table_form, table_entries=table_entries, current_step=step, total_steps=total_steps)

@blueprint.route('/delete_form/<int:form_id>', methods=['POST'])
@login_required
def delete_form(form_id):
    form = Forms.query.get(form_id)
    if form and form.user_id == current_user.id:
        TableEntry.query.filter_by(form_id=form.id).delete()
        db.session.delete(form)
        db.session.commit()
        flash('Form and associated table entries deleted successfully.', 'success')
    else:
        flash('Form not found or you do not have permission to delete it.', 'error')
    return redirect(url_for('forms_blueprint.view_forms'))

# Table entry
@blueprint.route('/delete_entry/<int:entry_id>', methods=['GET', 'POST'])
def delete_entry(entry_id):
    entry = TableEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully.', 'success')
    return redirect(url_for('forms_blueprint.submit_form', step=2))

@blueprint.route('/edit_entry/<int:entry_id>', methods=['GET', 'POST'])

@login_required
def edit_entry(entry_id):
    entry = TableEntry.query.get_or_404(entry_id)
    form = TableForm(obj=entry)

    if form.validate_on_submit():
        entry.item_no = form.item_no.data
        entry.description = form.description.data
        entry.quantity = form.quantity.data
        entry.unit = form.unit.data
        entry.unit_price = form.unit_price.data
        db.session.commit()
        flash('Entry updated successfully.', 'success')
        return redirect(url_for('forms_blueprint.submit_form', step=2))

    return render_template('forms/edit_entry.html', form=form, entry=entry)

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
