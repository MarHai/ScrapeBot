from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email
from scrapebot.emulate import RecipeStepTypeEnum


class RecipeForm(FlaskForm):
    name = StringField('Recipe name', validators=[DataRequired()])
    description = TextAreaField('Description')
    interval = IntegerField('Interval [minutes]', validators=[DataRequired()])
    cookies = BooleanField('Store cookies')
    active = BooleanField('Activated', default=True)
    submit = SubmitField('Save')


class RecipeDuplicateForm(FlaskForm):
    amount = IntegerField('Number of copies to create', validators=[DataRequired()], default=1)
    name = StringField('Pattern for newly created recipe\'s names', validators=[DataRequired()])
    description = TextAreaField('Description for all newly created recipes')
    active = BooleanField('Activate all newly created recipes (i.e., let them run)', default=True)
    user_privileges = BooleanField('Also copy user privileges', default=True)
    submit = SubmitField('Go ahead, create those copies (This is irreversible!)')


class RecipeStepForm(FlaskForm):
    type = SelectField('Type', choices=RecipeStepTypeEnum.choices(), coerce=RecipeStepTypeEnum.coerce)
    value = TextAreaField('Value (if needed)')
    use_random_item_instead_of_value = BooleanField('Randomly pick an item')
    use_data_item_instead_of_value = BooleanField('Use stored data as value')
    active = BooleanField('Activated', default=True)
    submit = SubmitField('Save')


class RecipeStepItemForm(FlaskForm):
    value = StringField('Item value', validators=[DataRequired()])
    submit = SubmitField('Save')


class InstanceForm(FlaskForm):
    name = StringField('Instance name')
    description = TextAreaField('Description')
    submit = SubmitField('Save')


class PrivilegeForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired(), Email()])
    allowed_to_edit = BooleanField('Allow editing')
    submit = SubmitField('Add privilege')
