from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired
from wtforms.widgets import CheckboxInput, ListWidget
from .models import Good


class StakeHoldersForm(FlaskForm):
    stakeholder = StringField('Stakeholder name:', validators=[DataRequired()])


class ProjectForm(FlaskForm):
    project = StringField('project', validators=[DataRequired()])
    law = BooleanField('law', default=True)
    # lawcb = CheckboxInput()
    # lawi = Input(input_type='checkbox')


class GoodsForm(FlaskForm):
    goods = StringField('Add a good:', validators=[DataRequired()])


class FunctionalRequirementsForm(FlaskForm):
    freq = StringField('Add a functional requirement:', validators=[DataRequired()])


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
    # test_choices = [('uno', 'one'),
    #                 ('dos', 'two'),
    #                 ('tres', 'three')]
    goods = Good.query.filter_by(project_id=3).all()
    good_choices = [(str(good.id), good.description) for good in goods]
    test_case = HardGoalsFormMultiple('Label', choices=good_choices)

# class EditorsList(FlaskForm):
#     editor_list = SelectField(u'Editors', coerce=int)
