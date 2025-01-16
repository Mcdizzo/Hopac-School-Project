from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FieldList, FormField, SelectField, FileField,TextAreaField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Email, InputRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired

#class LoginForm(FlaskForm):
    #email = StringField('Username', validators=[DataRequired()])
    #password = PasswordField('Password', validators=[DataRequired()])
    #submit = SubmitField('Login')

class SignupForm(FlaskForm):
    full_name = StringField('Fullname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    user_type = SelectField('User type', choices=[('','User-type'), ('Supervisor', 'Supervisor'), ('Staff', 'Staff')])
    spv_position = SelectField('User type', choices=[('Operational Manager', 'Operational Manager'), ('Principal', 'Principal'), ('Director','Director')])
    staff_job = SelectField('Staff Job', choices=[('Staff 1', 'Staff 1'), ('Staff 2', 'Staff 2')])

    password = PasswordField('Password', validators=[DataRequired()])
    re_pswd = PasswordField('Re-enter Password', validators=[DataRequired()])
    period = StringField('Review Period', validators=[DataRequired()])
    contact = StringField('Contact', validators=[DataRequired()])
    picture = FileField('Upload Picture', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    passkey = StringField('Passkey(for supervisor use only)')
    submit = SubmitField('Sign up')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[DataRequired()])
    question_type = SelectField('Question type', choices=[('text', 'Text'), ('scaling', 'Perfomance scaling')])
    
class QuestionSetForm(FlaskForm):
    question_title = StringField('Question title', validators=[DataRequired()])
    questions = FieldList(FormField(QuestionForm), min_entries=1)
    add_question =  SubmitField('Add question')
      
class DynamicQuestionForm(FlaskForm):
    question_sets = FieldList(FormField(QuestionSetForm), min_entries=1)
    add_question_set = SubmitField('Add Question Set')
    submit = SubmitField('Submit')

class DynamicStaffResponseForm(FlaskForm):
    submit = SubmitField('Submit')

class DynamicSupervisorResponseForm(FlaskForm):
    submit = SubmitField('Submit')

class AddAdminForm(FlaskForm):
    new_admin_email = StringField('Administrator Email', validators=[DataRequired()])
    add_admin = SubmitField('Add administrator')
    remove_admin = SubmitField('Remove administrator')

class DynamicPreviewForm(FlaskForm):
    submit = SubmitField('Submit')



class DatabaseForm(FlaskForm):
    # Field for the year (integer)
    year = IntegerField('Enter Year for New Database', validators=[InputRequired(), NumberRange(min=2025)])
    
    # Multiple selection field for tables (dynamic choice population)
    tables_to_retain = SelectMultipleField('Select Tables to Retain Data', coerce=int)
    
    # Submit button
    submit = SubmitField('Create Database')
