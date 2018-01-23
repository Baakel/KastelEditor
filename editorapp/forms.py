from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.widgets import Input, CheckboxInput



class StakeHoldersForm(FlaskForm):
    stakeholder = StringField('Stakeholder name:', validators=[DataRequired()])


class ProjectForm(FlaskForm):
    project = StringField('project', validators=[DataRequired()])
    law = BooleanField('law', default=True)
    lawcb = CheckboxInput()
    lawi = Input(input_type='checkbox')


class GoodsForm(FlaskForm):
    goods = StringField('Add a good:', validators=[DataRequired()])


class SoftGoalsForm(FlaskForm):
    sgoals = TextAreaField('sgoals', validators=[DataRequired()])
    priority = BooleanField('priority', default=False)


class EditorForm(FlaskForm):
    editor = StringField('Name:', validators=[DataRequired()])


class AccessForm(FlaskForm):
    revoke = StringField('Name:', validators=[DataRequired()])

# class EditorsList(FlaskForm):
#     editor_list = SelectField(u'Editors', coerce=int)
