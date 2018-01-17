from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length
from .models import Users


class StakeHoldersForm(FlaskForm):
    stakeholder = StringField('stakeholder', validators=[DataRequired()])


class ProjectForm(FlaskForm):
    project = StringField('project', validators=[DataRequired()])
    law = BooleanField('law', default=True)


class GoodsForm(FlaskForm):
    goods = StringField('goods', validators=[DataRequired()])


class SoftGoalsForm(FlaskForm):
    sgoals = TextAreaField('sgoals', validators=[DataRequired()])
    priority = BooleanField('priority', default=False)

# class EditorsList(FlaskForm):
#     editor_list = SelectField(u'Editors', coerce=int)
