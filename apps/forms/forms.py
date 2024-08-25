from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange, Email, Optional
from flask_ckeditor import CKEditorField

class CreateForm(FlaskForm):
    solicitation_number = StringField(
        'Solicitation Number', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: X123YZ-45-X-6789'}
    )
    title = StringField(
        'Title', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: XYZ Fuel Tanker Purge and Cleaning'}
    )
    company_name = StringField(
        'Company Name', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: XYZ Inc.'}
    )
    unique_entity_id = StringField(
        'Unique Entity ID', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: Y3FJQ6P7GND1'}
    )
    phone_number = StringField(
        'Phone Number', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Enter Phone Number'}
    )
    poc_email = StringField(
        'POC Email', 
        validators=[DataRequired(), Email()], 
        render_kw={'placeholder': 'Example: John.Doe@email.com'}
    )
    cage_code = StringField(
        'CAGE Code', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: L0VE9'}
    )
    ein_gst_hst_number = StringField(
        'EIN/GST-HST Number', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: 739878-346'}
    )
    poc = StringField(
        'POC', 
        validators=[DataRequired()], 
        render_kw={'placeholder': 'Example: Doe, John'}
    )
    technical_approach_documentation = CKEditorField(
        'Technical Approach Documentation',
        #render_kw={'placeholder': 'Paste Your Technical Approach Documentation Here'},
        validators=[Optional()]
    )
    past_performance = CKEditorField(
        'Past Performance',
        #render_kw={'Paste Your Past Performance Here'},
        validators=[Optional()]
    )
    submit = SubmitField('Save and Continue')
    
class TableForm(FlaskForm):
    item_no = IntegerField(
        'Item No',
        render_kw={'placeholder': '001'},
        validators=[DataRequired()]
    )
    description = TextAreaField(
        'Description', 
        validators=[DataRequired()],
        render_kw={'rows': 5, 'maxlength': 2048, 'placeholder': 'Enter Your Supplies / Services Here'}
    )
    quantity = IntegerField(
        'Quantity',
        render_kw={'placeholder': 'Enter The Quantity'},
        validators=[DataRequired(), NumberRange(min=1)]
    )
    unit = SelectField(
        'Unit', 
        choices=[('Month', 'Month'), ('Job', 'Job')],
        validators=[DataRequired()]
    )
    unit_price = FloatField(
        'Unit Price',
        render_kw={'placeholder': 'Job/Month Cost'},
        validators=[DataRequired(), NumberRange(min=0.01)]
    )
    submit = SubmitField('Add Item')
    edit = SubmitField('Edit Item')