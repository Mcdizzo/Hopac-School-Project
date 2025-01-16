from flask import send_from_directory
import os, re
from flask_mail import Message
from __init__ import mail
import mysql.connector
from mysql.connector import errorcode
import logging

#function for serving static files- based on the specific file folder root level

def serve_static(subdirectory, filename):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Navigate up two levels to project root
    static_dir = os.path.join(root_dir, 'static', subdirectory) 
    return send_from_directory(static_dir, filename)

#function for mail sending

def send_form_email(recipient, email_data):
    subject = "Your Form Submission"
    body = "Thank you for filling out the form. Here is a summary of your submission:\n\n"
    
    for key, value in email_data.items():
        clean_value = sanitize_input(value)
        body += f"{key}: {clean_value}\n"
    
    # Debugging: Print the email components to ensure they are correct
    print(f"Subject: {subject}")
    print(f"Recipient: {recipient}")
    print(f"Body: {body}")

    # Ensure recipient is not None and properly formatted
    if recipient:
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        mail.send(msg)
    else:
        print("Error: Recipient email is None or invalid.")
# cleaning the massage of any spaces or newlines

def sanitize_input(input_string):
    """Remove any characters that might cause issues in the email content."""
    return re.sub(r'[\r\n]', '', input_string) if input_string else 'N/A'



def create_mysql_database(new_db_name):
    """
    Creates a new MySQL database.
    """
    try:
        # Connect to MySQL server (no need to connect to a specific database)
        connection = mysql.connector.connect(
            host="localhost",    # Your MySQL host
            user="root",         # Your MySQL user
            password="your_password"  # Your MySQL password
        )
        
        cursor = connection.cursor()
        
        # Create the new database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {new_db_name}")
        connection.commit()
        
        logging.info(f"Database '{new_db_name}' created successfully or already exists.")
        
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        logging.error(f"Error: {err}")
        raise Exception(f"Error creating database: {err}")
