from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Admin, Student, Company
    is_active = db.Column(db.Boolean, default=True)
    resume = db.Column(db.String(255), nullable=True)
    cgpa = db.Column(db.Float, nullable=True)         

    applications = db.relationship('Application', backref='student', lazy=True)


class CompanyDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    hr_contact = db.Column(db.String(50))
    website = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)

    drives = db.relationship('PlacementDrive', backref='company', lazy=True)


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_details.id'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    eligibility_criteria = db.Column(db.Float, nullable=True)  # (None = open to all)
    date = db.Column(db.Date, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')

    applications = db.relationship('Application', backref='drive', lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    placement_drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    application_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='Applied')
    interview_date = db.Column(db.Date, nullable=True)       
    interview_notes = db.Column(db.String(255), nullable=True)  