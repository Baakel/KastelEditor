from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length
from .models import Users


class StakeHoldersForm(FlaskForm):
    stakeholder = StringField('stakeholder', validators=[DataRequired()])


class ProjectForm(FlaskForm):
    project = StringField('project', validators=[DataRequired()])
