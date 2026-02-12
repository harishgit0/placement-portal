from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()



class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)   # admin / company / student
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref='user', uselist=False)
    company = db.relationship('Company', backref='user', uselist=False)
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# ---------------- STUDENT
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    name = db.Column(db.String(100))
    roll_no = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    phone = db.Column(db.String(20))
    resume = db.Column(db.String(200))
    is_blacklisted = db.Column(db.Boolean, default=False)

# ---------------- COMPANY ----------------
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    company_name = db.Column(db.String(150))
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(150))
    approval_status = db.Column(db.String(20), default='Pending')
    is_blacklisted = db.Column(db.Boolean, default=False)

# ---------------- PLACEMENT DRIVE ----------------
class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'),nullable=False)
    job_title = db.Column(db.String(150))
    job_description = db.Column(db.Text)
    eligibility = db.Column(db.String(200))
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- APPLICATION ----------------
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'),nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'),nullable=False)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')


    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_application'),
    )