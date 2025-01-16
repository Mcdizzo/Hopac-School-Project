from flask import Blueprint, redirect, request, render_template, url_for, session, flash, current_app, g
from flask_wtf import FlaskForm
import os, base64
from __init__ import db
from models import users, supervisors, staff, questions, staff_responses, supervisor_responses
from forms import DynamicQuestionForm, AddAdminForm, DynamicStaffResponseForm, SignupForm, DynamicSupervisorResponseForm, DynamicPreviewForm, DatabaseForm
from wtforms import TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import mysql.connector
from sqlalchemy import create_engine, inspect
import logging

main = Blueprint('main', __name__)

# Landing Page Route

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
            if form.passkey.data == 'admin101':
               new_job_position = form.spv_position.data
               new_supervisor = supervisors(
                supervisor_id = new_user.user_id,
                job_position=new_job_position
                )
               db.session.add(new_supervisor)
            else:
                 return redirect(url_for('main.landing', message="Invalid passkey"))
        elif form.user_type.data == 'Staff':
            new_job_position = form.staff_job.data
            new_staff = staff(
                staff_id = new_user.user_id,
                job_position=new_job_position
                )
            db.session.add(new_staff)

        db.session.commit()
        return redirect(url_for('main.landing', message="Account created successfully! Login with your account"))
    else:
        return redirect(url_for('main.landing', message="could not create account try loggin in again"))



@main.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pswd']

        user = users.query.filter_by(email = email).first()
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            session['role'] = user.user_type
            return redirect(url_for('main.homepage'))
        else:
           return redirect(url_for('main.landing', message="Wrong passwrord or ID"))
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
            questions.question_text,
            questions.question_type
        )
        .order_by(questions.question_id.asc())
        .all()
    )

    print(question_data)
    for question in question_data:
        question_id = question[1]
        if question[3] == 'text':
            print("condition one is being executed")
            setattr(DynamicStaffResponseForm, f'staff_response_{question_id}', TextAreaField('Staff Response', validators=[DataRequired()]))
            #setattr(DynamicStaffResponseForm, f'admin_response_{question_id}', TextAreaField('Admin Response', validators=[DataRequired()]))
        else:
            print("condition two is being executed")
            setattr(DynamicStaffResponseForm, f'staff_scale_{question_id}', RadioField('Staff Scale', choices=[('poor', '1'), ('fair', '2'), ('good', '3'), ('best', '4')], default=None))
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

        #email_data = ' Thank you for submitting your respoonse you\'ll be notified when your supervisor reviews it'

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

        #send_form_email(email, email_data)

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



@main.route('/manage_admins', methods=['POST', 'GET'])
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
     return render_template('manage_admins.html', form = form)



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
            questions.question_text,
            questions.question_type
        )
        .order_by(questions.question_id.asc())
        .all()
    )

    print(question_data)
    for question in question_data:
        question_id = question[1]
        if question[3] == 'text':
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
            questions.question_text,
            questions.question_type
        )
        .order_by(questions.question_id.asc())
        .all()
    )

    
    for question in question_data:
        question_id = question[1]
        if question[3] == 'text':
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
def remove_question(question_id):
    id = question_id
    data = questions.query.get(id)
    if data:
        db.session.delete(data)
        db.session.commit()
    return redirect(url_for('main.form_preview'))

#this is the route for the staff to check the reviews from their supervisors.
@main.route('/staff_form_review/<int:staff_id>', methods=['GET', 'POST'])
def staff_form_review(staff_id):
    supervisor_response = supervisor_responses.query.filter_by(staff_id=staff_id).all()
    if supervisor_response:
        staff_member = users.query.get(staff_id)
        staff_response = staff_responses.query.filter_by(staff_id=staff_id).all()
        user_id = session.get('user_id')

        question_data = (
            db.session.query(
                questions.question_title,
                questions.question_id,
                questions.question_text,
                questions.question_type
            )
            .order_by(questions.question_id.asc())
            .all()
        )
    else:
        flash ('Sorry your supervisor hasn\'t reviewed your form yet')
        return redirect(url_for('main.homepage'))

    return render_template('staff_form_review.html', supervisor_response = supervisor_response ,staff_member=staff_member, staff_response=staff_response, question_data=question_data)


#managing the database
@main.route('/manage_database', methods=['GET','POST'])
def manage_database(): 
    return render_template('database.html')

#Data for database creation and switching
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'  # Your MySQL username
MYSQL_PASSWORD = '62645526'  # Your MySQL password
MYSQL_PORT = 3306  # Default MySQL port

logging.basicConfig(level=logging.DEBUG)

@main.route('/create_database', methods=['GET','POST'])
def create_database(): 
    form = DatabaseForm()

    # MySQL connection to get tables from the current database
    current_db = 'hopacdbms'  # Replace with your actual database name
    current_db_uri = 'mysql://root:62645526@localhost:3306/hopacdbms'
    current_engine = create_engine(current_db_uri)
    inspector = inspect(current_engine)
    tables = inspector.get_table_names()

    # Dynamically populate the form's SelectMultipleField with current tables
    form.tables_to_retain.choices = [(table, table) for table in tables]

    # Handle form submission
    if form.validate_on_submit():
        year = form.year.data
        # Use all tables from the current database
        tables_to_retain = tables  # List of all tables from the current database

        new_db_name = f"new_database_{year}"

        try:
            # Check if the new database already exists
            if database_exists(new_db_name):
                flash(f"Database '{new_db_name}' already exists.", "warning")
            else:
                logging.debug(f"Creating new database: {new_db_name}")
                # Create the new MySQL database
                create_mysql_database(new_db_name)
                
                # Copy the schema for all tables from the current database to the new one
                copy_tables_schema(current_db, new_db_name, tables_to_retain)
                
                # Optionally retain data for all tables
                retain_important_data(current_db, new_db_name, tables_to_retain)

                flash(f"Database '{new_db_name}' created successfully!", "success")
        except Exception as e:
            logging.error(f"An error occurred during database creation: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")
        
        return redirect(url_for('main.create_database'))

    return render_template('create_database.html', form=form)

@main.route('/switch_database', methods=['GET', 'POST'])
def switch_database():
    """
    Render the page to switch databases or handle the form submission.
    """
    if request.method == 'POST':
        db_name = request.form.get('databaseName')  # Get the selected database from the form

        if not db_name:
            flash("Please select a database.", "danger")
            return redirect(url_for('main.switch_database'))

        # Validate and switch database
        try:
            if not database_exists(db_name):
                flash(f"Database '{db_name}' does not exist.", "danger")
            else:
                # Switch database logic
                connection = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    port=MYSQL_PORT,
                    database=db_name
                )
                g.db_connection = connection  # Set the active connection
                flash(f"Switched to database '{db_name}' successfully!", "success")
        except Exception as e:
            logging.error(f"Error switching database: {e}")
            flash(f"An error occurred: {str(e)}", "danger")

        return redirect(url_for('main.manage_database'))

    # Fetch all available databases to populate the dropdown
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT
        )
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        cursor.close()
        connection.close()
    except Exception as e:
        logging.error(f"Error fetching database list: {e}")
        flash(f"Error fetching database list: {e}", "danger")
        databases = []

    # Render the template with available databases
    return render_template('switch_database.html', available_databases=databases)

#ROUTINES FOR DATABASE MANAGEMENT.
def before_request():
    """
    Before every request, check for the database connection.
    """
    # Skip for the switch_database route
    if request.endpoint == 'main.switch_database':
        return None

    db_name = request.headers.get("X-Database-Name")
    if not db_name:
        flash("Database name is required to process the request.", "danger")
        return redirect(url_for("main.switch_database"))  # Redirect to the switch database page

    if not database_exists(db_name):
        flash(f"Database '{db_name}' does not exist.", "danger")
        return redirect(url_for("main.switch_database"))

    try:
        g.db_connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            database=db_name
        )
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to database '{db_name}': {err}")
        flash(f"Error connecting to database: {err}", "danger")
        return redirect(url_for("main.switch_database"))



def teardown_request(exception):
    """
    Close the database connection after the request is processed.
    """
    db_connection = getattr(g, "db_connection", None)
    if db_connection:
        db_connection.close()

def database_exists(db_name):
    """
    Check if a MySQL database already exists.
    """
    try:
        logging.debug(f"Checking existence of database: {db_name}")
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT
        )
        cursor = connection.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        return result is not None
    except mysql.connector.Error as err:
        logging.error(f"Error checking database existence: {err}")
        return False


def create_mysql_database(new_db_name):
    """
    Creates a new MySQL database.
    """
    try:
        logging.debug(f"Attempting to create database: {new_db_name}")
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {new_db_name}")
        connection.commit()
        cursor.close()
        connection.close()
        logging.info(f"Database '{new_db_name}' created successfully.")
    except mysql.connector.Error as err:
        logging.error(f"Error creating database: {err}")
        raise Exception(f"Error creating database: {err}")


def copy_tables_schema(source_db, target_db, tables_to_copy):
    """
    Copy the schema (structure) of selected tables from the source to the target database.
    This function ensures referenced tables are created first.
    """
    try:
        # Connect to source and target databases
        source_conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            database=source_db
        )
        target_conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            database=target_db
        )

        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()

        # Disable foreign key checks in the target database temporarily
        target_cursor.execute("SET foreign_key_checks = 0")

        # Loop through each table to copy its schema
        for table in tables_to_copy:
            logging.debug(f"Copying schema for table: {table}")
            
            # Get the CREATE TABLE statement from the source database
            source_cursor.execute(f"SHOW CREATE TABLE {table}")
            create_table_stmt = source_cursor.fetchone()[1]

            logging.debug(f"CREATE TABLE statement for {table}: {create_table_stmt}")

            # Execute the CREATE TABLE statement on the target database
            target_cursor.execute(create_table_stmt)
        
        # Commit changes to the target database
        target_conn.commit()

        # Re-enable foreign key checks after the tables are copied
        target_cursor.execute("SET foreign_key_checks = 1")

        # Close cursors and connections
        source_cursor.close()
        target_cursor.close()
        source_conn.close()
        target_conn.close()

        logging.info(f"Schema copied for tables: {tables_to_copy}")
    except mysql.connector.Error as err:
        logging.error(f"Error copying schema for tables: {err}")
        raise Exception(f"Error copying schema for tables: {err}")



def retain_important_data(source_db, target_db, tables_to_retain):
    """
    Retain data for selected tables from the source database to the new database.
    This function disables foreign key checks temporarily to allow data insertion even if constraints are violated.
    """
    try:
        logging.debug(f"Retaining data for tables: {tables_to_retain}")
        
        # Connect to source and target databases
        source_conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            database=source_db
        )
        target_conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            database=target_db
        )

        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()

        # Disable foreign key checks in the target database temporarily
        target_cursor.execute("SET foreign_key_checks = 0")

        # Loop through each table to copy its data
        for table in tables_to_retain:
            logging.debug(f"Copying data for table: {table}")
            
            # Get the data from the source table
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()

            if rows:  # Ensure there's data to copy
                # Construct the INSERT query
                placeholders = ', '.join(['%s'] * len(rows[0]))  # Adjust for column count
                insert_query = f"INSERT INTO {table} VALUES ({placeholders})"

                # Insert the data into the target table
                target_cursor.executemany(insert_query, rows)
            else:
                logging.debug(f"No data found in table: {table}")

        # Commit changes to the target database
        target_conn.commit()

        # Re-enable foreign key checks after the data is inserted
        target_cursor.execute("SET foreign_key_checks = 1")

        # Close cursors and connections
        source_cursor.close()
        target_cursor.close()
        source_conn.close()
        target_conn.close()

        logging.info(f"Data retained for tables: {tables_to_retain}")
    except mysql.connector.Error as err:
        logging.error(f"Error retaining data for tables: {err}")
        raise Exception(f"Error retaining data for tables: {err}")
