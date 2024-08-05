# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Email, Optional
from flask_ckeditor import CKEditorField

class CreateForm(FlaskForm):    
    solicitation_number = StringField('Solicitation Number', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    company_name = StringField('Company Name', validators=[DataRequired()])
    unique_entity_id = StringField('Unique Entity ID', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    poc_email = StringField('POC Email', validators=[DataRequired(), Email()])
    cage_code = StringField('CAGE Code', validators=[DataRequired()])
    ein_gst_hst_number = StringField('EIN/GST-HST Number', validators=[DataRequired()])
    poc = StringField('POC', validators=[DataRequired()])
    technical_approach_documentation = CKEditorField('Technical Approach Documentation', validators=[Optional()])
    past_performance = CKEditorField('Past Performance', validators=[Optional()])
    submit = SubmitField('Save and Continue')
    
class TableForm(FlaskForm):
    item_no = IntegerField('Item No', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={'rows': 5, 'maxlength': 2048})
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    unit = StringField('Unit', validators=[DataRequired()])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Add Item')
    edit = SubmitField('Edit Item')

    