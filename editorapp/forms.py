from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length


class StakeHoldersForm(FlaskForm):
    stakeholder = StringField('stakeholder', validators=[DataRequired()])