from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from models import db, User, Fee, Receipt, FeeTemplate
from datetime import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import zipfile
import csv
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    students = User.query.filter_by(role='student').all()
    search = request.args.get('search', '')
    if search:
        fees = Fee.query.join(User).filter(User.name.contains(search)).all()
    else:
        fees = Fee.query.all()
    return render_template('admin_dashboard.html', students=students, fees=fees)

@admin_bp.route('/add_fee', methods=['POST'])
@login_required
def add_fee():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    student_id = request.form.get('student_id')
    title = request.form.get('title', 'Fee')
    amount = float(request.form['amount'])
    due_date_str = request.form['due_date']
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    apply_to_all = request.form.get('apply_to_all') == 'on'

    if apply_to_all:
        # Create fee template for future students
        fee_template = FeeTemplate(title=title, amount=amount, due_date=due_date)
        db.session.add(fee_template)
        db.session.commit()
        
        # Assign to all existing students
        students = User.query.filter_by(role='student').all()
        for student in students:
            new_fee = Fee(student_id=student.id, title=title, amount=amount, due_date=due_date)
            db.session.add(new_fee)
        db.session.commit()
        flash(f'Fee "{title}" assigned to all {len(students)} students and will apply to new registrations!', 'success')
    elif student_id:
        # Assign to single student
        new_fee = Fee(student_id=student_id, title=title, amount=amount, due_date=due_date)
        db.session.add(new_fee)
        db.session.commit()
        flash('Fee added successfully!', 'success')
    else:
        flash('Please select a student or choose to apply to all students.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/download_receipt/<int:fee_id>')
@login_required
def download_receipt(fee_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    receipt = Receipt.query.filter_by(fee_id=fee_id).first()
    if receipt:
        return send_file(receipt.receipt_file_path, as_attachment=True)
    flash('Receipt not found', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/download_all_receipts')
@login_required
def download_all_receipts():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    receipts = Receipt.query.all()
    zip_path = os.path.join(current_app.root_path, 'all_receipts.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for receipt in receipts:
            zipf.write(receipt.receipt_file_path, os.path.basename(receipt.receipt_file_path))
    return send_file(zip_path, as_attachment=True)

@admin_bp.route('/export_csv')
@login_required
def export_csv():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    fees = Fee.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student', 'Amount', 'Due Date', 'Payment Date', 'Status', 'Penalty'])
    for fee in fees:
        writer.writerow([fee.student.name, fee.amount, fee.due_date.strftime('%Y-%m-%d'), fee.payment_date.strftime('%Y-%m-%d') if fee.payment_date else 'N/A', fee.status, fee.penalty_amount])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='fees.csv')