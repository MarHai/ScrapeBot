from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField


class DownloadForm(FlaskForm):
    instance_list = TextAreaField('Instances')
    recipe_list = TextAreaField('Recipes')
    submit = SubmitField('Download this data now')
