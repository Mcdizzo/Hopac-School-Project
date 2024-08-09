from flask import Blueprint, redirect, request, render_template, url_for, session, flash, current_app
#from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
import os, base64
from __init__ import db
from models import users, supervisors, staff, questions, staff_responses, supervisor_responses
from forms import DynamicQuestionForm, AddAdminForm, DynamicStaffResponseForm, SignupForm, DynamicSupervisorResponseForm, DynamicPreviewForm
from wtforms import TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from routines import send_form_email

main = Blueprint('main', __name__)



@main.route('/')
def landing():
    form = SignupForm()
    return render_template('login_page.html', form=form)



@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        print('cowabanga')
        form = SignupForm()
        print(form.data)

        # for the uploaded picture
        file = form.picture.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])

        file.save(file_path)
        
        # Convert file content to binary
        with open(file_path, 'rb') as f:
            picture_data = f.read()

        new_user = users(
            user_id= form.id.data,
            full_name= form.full_name.data,
            password_hash= form.password.data,
            user_type= form.user_type.data,
            review_period= form.period.data,
            Contact= form.contact.data,
            email= form.email.data,
            picture= picture_data
        )

        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        if form.user_type.data == 'Supervisor':
            new_job_position = form.spv_position.data
            new_supervisor = supervisors(supervisor_id=form.id.data, job_position=new_job_position)
            db.session.add(new_supervisor)
        elif form.user_type.data == 'Staff':
            new_job_position = form.staff_job.data
            new_staff = staff(staff_id=form.id.data, job_position=new_job_position)
            db.session.add(new_staff)

        db.session.commit()
        return redirect(url_for('main.landing', message="Account created successfully! Login with your account"))
    else:
        return redirect(url_for('main.landing', message="could not create account try loggin in again"))



@main.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_id = request.form['usrId']
        password = request.form['pswd']

        user = users.query.filter_by(user_id=user_id).first()
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            session['role'] = user.user_type
            return redirect(url_for('main.homepage'))
        flash('Invalid ID or password', 'error')
    else:
     return render_template('login_page.html')



@main.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('main.landing'))



@main.route('/homepage', methods=['POST', 'GET'])
def homepage():
    user_id = session.get('user_id')
    logged_in_user = users.query.get(user_id)

    print(logged_in_user)
    
    if logged_in_user.user_type == 'Staff':
        staff_user = staff.query.get(user_id)

        jobtitle = staff_user.job_position
    else:
        supervisor_user = supervisors.query.get(user_id)

        jobtitle = supervisor_user.job_position

    return render_template('homepage.html', user=logged_in_user, jobtitle=jobtitle)



@main.route('/add_question', methods=['POST', 'GET'])
def add_question():
    form = DynamicQuestionForm()
    if request.method == 'POST':
        
        if form.add_question_set.data:
            form.question_sets.append_entry()
            
        
        for set_form in form.question_sets:
            if set_form.add_question.data:
                set_form.questions.append_entry()
                
        
        if form.submit.data:

            for set_form in form.question_sets:
                question_title = set_form.question_title.data
                for question_form in set_form.questions:
                    question_text = question_form.question_text.data
                    question_type = question_form.question_type.data
                    
                    
                    new_question = questions(
                        question_title=question_title,
                        question_text=question_text,
                        question_type=question_type
                    )
                    db.session.add(new_question)
                    db.session.commit()
            flash('Questions added successfully!', 'success')
            return redirect(url_for('main.add_question'))
    else:
        userType = session.get('role')
        if userType == 'Staff':
           flash('You need to be an administrator to access this page')
           return redirect(url_for('main.homepage'))
        else:
         return render_template('Question-setting.html', form=form)



@main.route('/form', methods=['POST', 'GET'])
def questions_view():
    question_data = (
        db.session.query(
            questions.question_title,
            questions.question_id,
            questions.form_id,
            questions.question_text,
            questions.question_type
        )
        .order_by(questions.question_id.asc())
        .all()
    )

    
    for question in question_data:
        question_id = question[1]
        if question[4] == 'text':
            setattr(DynamicStaffResponseForm, f'staff_response_{question_id}', TextAreaField('Staff Response', validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_response_{question_id}', TextAreaField('Admin Response', validators=[DataRequired()]))
        else:
            setattr(DynamicStaffResponseForm, f'staff_scale_{question_id}', RadioField('Staff Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_scale_{question_id}', RadioField('Admin Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], validators=[DataRequired()]))
            setattr(DynamicStaffResponseForm, f'staff_comment_{question_id}', TextAreaField('Staff Comment', validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_comment_{question_id}', TextAreaField('Admin Comment', validators=[DataRequired()]))

    form = DynamicStaffResponseForm(request.form)

    if request.method == 'POST':
        user_id = session.get('user_id')
    
        if user_id:
        # Query the database to get the user's email
         user = users.query.filter_by(user_id=user_id).first()
        if user:
            email = user.email
        else:
            email = None
            print('User not found.')

        # the body of the email to be sent

        email_data = request.form.to_dict()

        for question in question_data:
            question_id = question[1]
            staff_response = request.form.get(f'staff_response_{question_id}')
            #admin_response = request.form.get(f'admin_response_{question_id}')
            staff_scale = request.form.get(f'staff_scale_{question_id}')
            #admin_scale = request.form.get(f'admin_scale_{question_id}')
            staff_comment = request.form.get(f'staff_comment_{question_id}')
            #admin_comment = request.form.get(f'admin_comment_{question_id}')

            if staff_response or staff_scale is not None:
                new_staff_response = staff_responses(
                    staff_id=user_id,
                    question_id=question_id,
                    response_text=staff_response,
                    response_rating=staff_scale,
                    comment = staff_comment
                )
                db.session.add(new_staff_response)

            #if admin_comment or admin_scale is not None:
             #   new_admin_response = supervisor_responses(
              #      supervisor_id=user_id,
               #     question_id=question_id,
                #    comment = admin_comment,
                 #   response_rating=admin_scale,
                
                #)
                #db.session.add(new_admin_response)

        db.session.commit()

        # sending the email to show a preview of what the user has filled.

        send_form_email(email, email_data)

        flash('Thank you for filling the form, it has been submitted successfully!!', 'success')
        return redirect(url_for('main.homepage'))

    return render_template('form.html', question_data=question_data, form=form)



@main.route('/return_to_form')
def form_return():
    pass
    #previous_form_data = 



@main.route('/return_to_homepage')
def home_return():
    return redirect(url_for('main.homepage'))



@main.route('/add_admin', methods=['POST', 'GET'])
def add_admin():
    form = AddAdminForm()
    if request.method == "POST":
            new_admin_email = request.form.get('new_admin_email')

            user = users.query.filter_by(email=new_admin_email ).first()
            if form.add_admin.data:
                print('cowabanga')
                if user:
                    if user.user_type == 'Staff':
                        user.user_type = 'Supervisor'
                        print('user_type has been changed')
                        db.session.add(user)
                        db.session.commit()
                        print('user_type has been changed')

                        staff_member = staff.query.filter_by(staff_id=user.user_id ).first()
                        if staff_member:
                            db.session.delete(staff_member)
                            db.session.commit()
                            print('cowabanga')
                        new_supervisor = supervisors(supervisor_id=user.user_id, job_position=staff_member.job_position)
                        db.session.add(new_supervisor)
                        db.session.commit()
                    else:
                        flash('User is not registred as a staff member')
                else:
                    flash('user is not found in database')
            return redirect(url_for('main.add_admin'))      
    else:
     return render_template('add_admin.html', form = form)



@main.route('/form_list_review', methods=['POST','GET'])
def review_form_list():
    if request.method == "GET":
        id = session.get('user_id')
        user = users.query.filter_by(user_id=id).first()
        if user:
            if user.user_type == "Supervisor":
                supervisor = supervisors.query.filter_by(supervisor_id=id).first()
                
                position = supervisor.job_position

                staffs = staff.query.all()
                staff_user = users.query.filter_by(user_type = 'Staff').all()
        else:
            flash('User not found, try logging in again')

    return render_template('form_review_list.html', position = position, staffs=staffs, staff_user=staff_user)

@main.route('/form_review/<int:staff_id>', methods=['GET', 'POST'])
def review_form(staff_id):
    staff_member = users.query.get(staff_id)
    staff_response = staff_responses.query.filter_by(staff_id=staff_id).all()
    user_id = session.get('user_id')

    question_data = (
        db.session.query(
            questions.question_title,
            questions.question_id,
            questions.form_id,
            questions.question_text,
            questions.question_type
        )
        .order_by(questions.question_id.asc())
        .all()
    )

    
    for question in question_data:
        question_id = question[1]
        if question[4] == 'text':
            #setattr(DynamicResponseForm, f'staff_response_{question_id}', TextAreaField('Staff Response', validators=[DataRequired()]))
            setattr(DynamicSupervisorResponseForm, f'admin_response_{question_id}', TextAreaField('Admin Response', validators=[DataRequired()]))
        else:
            #setattr(DynamicResponseForm, f'staff_scale_{question_id}', RadioField('Staff Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], validators=[DataRequired()]))
            setattr(DynamicSupervisorResponseForm, f'admin_scale_{question_id}', RadioField('Admin Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], validators=[DataRequired()]))
            #setattr(DynamicResponseForm, f'staff_response_{question_id}', TextAreaField('Staff Response', validators=[DataRequired()]))
            setattr(DynamicSupervisorResponseForm, f'admin_comment_{question_id}', TextAreaField('Admin Comment', validators=[DataRequired()]))

    form = DynamicSupervisorResponseForm(request.form)

    if request.method == 'POST':

        for question in question_data:
            question_id = question[1]
            #staff_response = request.form.get(f'staff_response_{question_id}')
            #admin_response = request.form.get(f'admin_response_{question_id}')
            #staff_scale = request.form.get(f'staff_scale_{question_id}')
            admin_scale = request.form.get(f'admin_scale_{question_id}')
            #staff_comment = request.form.get(f'staff_comment_{question_id}')
            admin_comment = request.form.get(f'admin_comment_{question_id}')

            if admin_comment or admin_scale is not None:
                new_admin_response = supervisor_responses(
                    supervisor_id=user_id,
                    question_id=question_id,
                    staff_id = staff_id,
                    comment = admin_comment,
                    response_rating=admin_scale,
                )
                db.session.add(new_admin_response)

        db.session.commit()
        flash('review submitted', 'success')

        return redirect(url_for('main.review_form_list'))
    else:
        return render_template('review_form.html', form=form, staff_member=staff_member, staff_response=staff_response, question_data=question_data)


@main.route('/preview', methods=['GET','POST'])
def form_preview():

    question_data = (
        db.session.query(
            questions.question_title,
            questions.question_id,
            questions.form_id,
            questions.question_text,
            questions.question_type
        )
        .order_by(questions.question_id.asc())
        .all()
    )

    
    for question in question_data:
        question_id = question[1]
        if question[4] == 'text':
            setattr(DynamicPreviewForm, f'staff_response_{question_id}', TextAreaField('Staff Response', validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_response_{question_id}', TextAreaField('Admin Response', validators=[DataRequired()]))
        else:
            setattr(DynamicPreviewForm, f'staff_scale_{question_id}', RadioField('Staff Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_scale_{question_id}', RadioField('Admin Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], validators=[DataRequired()]))
            setattr(DynamicPreviewForm, f'staff_comment_{question_id}', TextAreaField('Staff Comment', validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_comment_{question_id}', TextAreaField('Admin Comment', validators=[DataRequired()]))

    form = DynamicPreviewForm(request.form)

    return render_template('preview.html', question_data=question_data, form=form)

   
@main.route('/question_removed/<int:question_id>', methods=['GET','POST'])
def remove_question():
    pass