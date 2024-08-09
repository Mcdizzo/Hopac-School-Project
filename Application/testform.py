from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

class test(FlaskForm):
    question_text = StringField('Question', validators=[DataRequired()])
    question_type = SelectField('Question type', choices=[('text', 'Text'), ('scaling', 'Perfomance scaling')])