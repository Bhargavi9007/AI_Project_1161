from flask import Flask, render_template, redirect, url_for, flash, request, send_file, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Fee, Receipt, FeeTemplate
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import zipfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fee_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RECEIPTS_FOLDER'] = os.path.join(app.root_path, 'receipts')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(student_bp, url_prefix='/student')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/receipts/<filename>')
@login_required
def download_receipt(filename):
    return send_from_directory(app.config['RECEIPTS_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)