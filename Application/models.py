
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
#from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from __init__ import db
# this is a test to see if the git worked
class users (db.Model):
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    full_name = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(8), unique=True, nullable=False)
    user_type = db.Column(db.String(20))
    review_period = db.Column(db.Integer, nullable=False)
    Contact = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    picture = db.Column(db.LargeBinary, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class supervisors (db.Model):
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False)
    job_position = db.Column(db.String(50))

class staff (db.Model):
    staff_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False)
    job_position = db.Column(db.String(50))

class forms (db.Model):
    form_id = db.Column(db.Integer, primary_key=True)
    form_name = db.Column(db.String(20), nullable=False)
    supervisor_ID = db.Column(db.Integer, db.ForeignKey('supervisors.supervisor_id'), nullable=False)

class questions (db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.form_id'), nullable=False)
    question_title = db.Column(db.String(20), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)

class staff_responses (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    response_rating = db.Column(db.String(10), nullable=False)
    response_date = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable=False)

class supervisor_responses (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.supervisor_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    response_rating = db.Column(db.String(10), nullable=False)
    response_date = db.Column(db.DateTime, default=datetime.utcnow)
