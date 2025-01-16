
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
#from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from __init__ import db

class users(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), unique=True, nullable=False)
    user_type = db.Column(db.String(255))
    review_period = db.Column(db.Integer, nullable=False)
    Contact = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    picture = db.Column(db.LargeBinary(16777215), nullable=True)
    
    # Define relationships without conflicting backrefs
    supervisor = db.relationship('supervisors', uselist=False, back_populates='user')
    staff = db.relationship('staff', uselist=False, back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class supervisors(db.Model):
    __tablename__ = "supervisors"
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, primary_key=True)
    job_position = db.Column(db.String(255))
    
    # Relationships
    user = db.relationship('users', back_populates='supervisor')
    responses = db.relationship('supervisor_responses', backref='supervisor', lazy=True)
    forms = db.relationship('forms', backref='supervisor', lazy=True)

class staff(db.Model):
    __tablename__ = "staff"
    staff_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False)
    job_position = db.Column(db.String(255))
    
    # Relationships
    user = db.relationship('users', back_populates='staff')
    responses = db.relationship('staff_responses', backref='staff', lazy=True)
    forms = db.relationship('forms', backref='staff', lazy=True)

class forms(db.Model):
    __tablename__ = "forms"
    form_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    form_name = db.Column(db.String(255), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.supervisor_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)

    # Relationships
    #questions = db.relationship('questions', backref='form', lazy=True)

class questions(db.Model):
    __tablename__ = "questions"
    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_title = db.Column(db.String(255), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(255), nullable=False)

class staff_responses(db.Model):
    __tablename__ = "staff_responses"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    response_text = db.Column(db.Text, nullable = True)
    response_rating = db.Column(db.String(255), nullable = True)
    response_date = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable = True)

class supervisor_responses(db.Model):
    __tablename__ = "supervisor_responses"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.supervisor_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    comment = db.Column(db.Text, nullable = True)
    response_rating = db.Column(db.String(255), nullable = True)
    response_date = db.Column(db.DateTime, default=datetime.utcnow)




