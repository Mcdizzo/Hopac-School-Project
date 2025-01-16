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

# Sign Up Route
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            form = SignupForm()
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

            # Check user type for additional info
            if form.user_type.data == 'Supervisor':
                if form.passkey.data != 'admin101':
                    flash("Invalid passkey", 'error')
                    return redirect(url_for('main.landing'))

                new_supervisor = supervisors(supervisor_id=new_user.user_id, job_position=form.spv_position.data)
                db.session.add(new_supervisor)
            elif form.user_type.data == 'Staff':
                new_staff = staff(staff_id=new_user.user_id, job_position=form.staff_job.data)
                db.session.add(new_staff)

            db.session.commit()
            flash("Account created successfully! Login with your account", 'success')
            return redirect(url_for('main.landing'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}. Please try again.", 'error')
            return redirect(url_for('main.landing'))
    return redirect(url_for('main.landing', message="could not create account try logging in again"))

# Login Route
@main.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['pswd']

            user = users.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session['user_id'] = user.user_id
                session['role'] = user.user_type
                return redirect(url_for('main.homepage'))
            else:
                flash('Invalid ID or password', 'error')
        except Exception as e:
            flash(f"Login error: {str(e)}", 'error')
    return render_template('login_page.html')

# Logout Route
@main.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('main.landing'))

# Homepage Route
@main.route('/homepage', methods=['POST', 'GET'])
def homepage():
    try:
        user_id = session.get('user_id')
        logged_in_user = users.query.get(user_id)
        
        if logged_in_user.user_type == 'Staff':
            staff_user = staff.query.get(user_id)
            jobtitle = staff_user.job_position
        else:
            supervisor_user = supervisors.query.get(user_id)
            jobtitle = supervisor_user.job_position

        return render_template('homepage.html', user=logged_in_user, jobtitle=jobtitle)

    except Exception as e:
        flash(f"Error loading homepage: {str(e)}", 'error')
        return redirect(url_for('main.landing'))

# Add Question Route
@main.route('/add_question', methods=['POST', 'GET'])
def add_question():
    form = DynamicQuestionForm()
    try:
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
            flash('You need to be an administrator to access this page', 'error')
            return redirect(url_for('main.homepage'))
        return render_template('Question-setting.html', form=form)

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}. Please try again.", 'error')
        return redirect(url_for('main.add_question'))

# Review Form Route (for Staff to review supervisor responses)
@main.route('/staff_form_review/<int:staff_id>', methods=['GET', 'POST'])
def staff_form_review(staff_id):
    try:
        supervisor_response = supervisor_responses.query.filter_by(staff_id=staff_id).all()
        if not supervisor_response:
            flash("Sorry, your supervisor hasn't reviewed your form yet", 'warning')
            return redirect(url_for('main.homepage'))

        staff_member = users.query.get(staff_id)
        staff_response = staff_responses.query.filter_by(staff_id=staff_id).all()

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

        return render_template('staff_form_review.html', supervisor_response=supervisor_response, staff_member=staff_member, staff_response=staff_response, question_data=question_data)
    
    except Exception as e:
        flash(f"Error loading review: {str(e)}", 'error')
        return redirect(url_for('main.homepage'))

# Remove Question Route
@main.route('/question_removed/<int:question_id>', methods=['GET','POST'])
def remove_question(question_id):
    try:
        question_to_remove = questions.query.get(question_id)
        if question_to_remove:
            db.session.delete(question_to_remove)
            db.session.commit()
            flash("Question removed successfully", 'success')
        else:
            flash("Question not found", 'warning')
        return redirect(url_for('main.form_preview'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}. Could not remove the question", 'error')
        return redirect(url_for('main.form_preview'))

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
