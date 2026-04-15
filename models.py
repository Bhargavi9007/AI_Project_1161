from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'student'

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False, default='Fee')  # e.g., "Semester Fee", "Lab Fee"
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='Pending')  # Paid, Pending, Late
    penalty_amount = db.Column(db.Float, default=0.0)

    student = db.relationship('User', backref=db.backref('fees', lazy=True))

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fee_id = db.Column(db.Integer, db.ForeignKey('fee.id'), nullable=False)
    receipt_file_path = db.Column(db.String(200), nullable=False)

    fee = db.relationship('Fee', backref=db.backref('receipt', uselist=False))


class FeeTemplate(db.Model):
    """Template for fees that apply to all students"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default='Fee')  # e.g., "Semester Fee"
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=db.func.now())
