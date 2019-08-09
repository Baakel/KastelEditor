from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SelectMultipleField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired
from wtforms.widgets import CheckboxInput, ListWidget


class StakeHoldersForm(FlaskForm):
    stakeholder = StringField('Stakeholder name:', validators=[DataRequired()])


class ProjectForm(FlaskForm):
    project = StringField('Create a project with a unique name:', validators=[DataRequired()])
    law = BooleanField('law', default=True)
    # lawcb = CheckboxInput()
    # lawi = Input(input_type='checkbox')


class GoodsForm(FlaskForm):
    goods = StringField('Add an asset:', validators=[DataRequired()])
    stakeholders_list = SelectField()


class FunctionalRequirementsForm(FlaskForm):
    freq = StringField('Add a functional requirement:', validators=[DataRequired()])
    subserv = StringField('Add a Component to Handle the requirements')
    subservice_multiple_select = SelectField()


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
    # goods = Good.query.filter_by(project_id=3).all()
    # good_choices = [(str(good.id), good.description) for good in goods]
    # test_case = HardGoalsFormMultiple('Label', choices=good_choices)
    pass


class BbmForm(FlaskForm):
    selections = SelectField('Desired Mechanism', coerce=int, validators=[DataRequired()])
        # SelectField('Desired Mechanism', coerce=int, validators=[DataRequired()])


class ActorsForm(FlaskForm):
    actor = StringField('Actor name:', validators=[DataRequired()])
    component_access = SelectField('Access to Components', choices=[(1, 'External'), (2, 'User'), (3, 'Admin')])
    component_access_list = SelectField()


class AttackersForm(FlaskForm):
    attacker = StringField('Attacker name:', validators=[DataRequired()])
    softgoals_list = SelectField()