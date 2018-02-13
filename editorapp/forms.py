from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired
from wtforms.widgets import Input, CheckboxInput, ListWidget


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


class HardGoalsFormMultiple(SelectMultipleField):

    # def __init__(self, choices):
    #     self.choices = choices
    #
    # def createcheckboxes(self, choices):
    #     checkboxes = SelectMultipleField(
    #         'what is this?',
    #         choices=choices,
    #         option_widget=CheckboxInput(),
    #         widget= ListWidget(prefix_label=False)
    #     )

    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class HardGoalsForm(FlaskForm):
    # authenticity = BooleanField(default=False)
    # confidentiality = BooleanField(default=False)
    # integrity = BooleanField(default=False)
    test = HardGoalsFormMultiple('label', choices=2)

# class EditorsList(FlaskForm):
#     editor_list = SelectField(u'Editors', coerce=int)
