# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps import db

class Forms(db.Model):
    __tablename__ = 'Forms'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    
    solicitation_number = db.Column(db.String(64))
    title = db.Column(db.String(256))
    company_name = db.Column(db.String(128))
    unique_entity_id = db.Column(db.String(64))
    phone_number = db.Column(db.String(20))
    poc_email = db.Column(db.String(64))
    cage_code = db.Column(db.String(20))
    ein_gst_hst_number = db.Column(db.String(20))
    poc = db.Column(db.String(64))
    technical_approach_documentation = db.Column(db.Text)
    past_performance = db.Column(db.Text)

    user = db.relationship('Users', backref=db.backref('forms', lazy=True))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)

    def __repr__(self):
        return f'<Form {self.id} for {self.company_name}>'

class TableEntry(db.Model):
    __tablename__ = 'TableEntries'

    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('Forms.id'), nullable=False)
    item_no = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(2048), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(64), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    @property
    def ext_price(self):
        return self.quantity * self.unit_price

    def __repr__(self):
        return f'<TableEntry {self.id} for Form {self.form_id}>'