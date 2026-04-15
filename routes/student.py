from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from models import db, Fee, Receipt
from datetime import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        return redirect(url_for('home'))
    fees = Fee.query.filter_by(student_id=current_user.id).all()
    return render_template('student_dashboard.html', fees=fees)

@student_bp.route('/pay_fee/<int:fee_id>', methods=['POST'])
@login_required
def pay_fee(fee_id):
    if current_user.role != 'student':
        return redirect(url_for('home'))
    fee = Fee.query.get_or_404(fee_id)
    if fee.student_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('student.dashboard'))
    fee.payment_date = datetime.utcnow()
    if fee.payment_date > fee.due_date:
        fee.penalty_amount = fee.amount * 0.05
    fee.status = 'Paid'
    db.session.commit()
    # Generate receipt
    generate_receipt(fee)
    flash('Payment successful!', 'success')
    return redirect(url_for('student.dashboard'))

def generate_receipt(fee):
    filename = f"receipt_{fee.id}.pdf"
    if not os.path.exists(current_app.config['RECEIPTS_FOLDER']):
        os.makedirs(current_app.config['RECEIPTS_FOLDER'], exist_ok=True)
    filepath = os.path.join(current_app.config['RECEIPTS_FOLDER'], filename)
    width, height = letter
    c = canvas.Canvas(filepath, pagesize=letter)

    # Header
    c.setFillColor(colors.HexColor('#0d3b66'))
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 24)
    c.drawString(50, height - 70, 'University Fee Receipt')
    c.setFont('Helvetica', 10)
    c.drawString(50, height - 90, 'University of Excellence')
    c.drawString(50, height - 105, 'Fee Management Office')

    # Receipt data box
    c.setStrokeColor(colors.HexColor('#ffd60a'))
    c.setLineWidth(1.5)
    c.roundRect(40, height - 335, width - 80, 190, 12, stroke=1, fill=0)

    c.setFillColor(colors.HexColor('#23395b'))
    c.setFont('Helvetica-Bold', 12)
    c.drawString(60, height - 140, 'Receipt ID:')
    c.drawString(60, height - 165, 'Student Name:')
    c.drawString(60, height - 190, 'Fee Title:')
    c.drawString(60, height - 215, 'Fee Amount:')
    c.drawString(60, height - 240, 'Penalty:')
    c.drawString(60, height - 265, 'Total Charged:')
    c.drawString(60, height - 290, 'Payment Date:')
    c.drawString(60, height - 315, 'Status:')

    c.setFillColor(colors.HexColor('#0d3b66'))
    c.setFont('Helvetica', 12)
    c.drawString(220, height - 140, f"#{fee.id}")
    c.drawString(220, height - 165, fee.student.name)
    c.drawString(220, height - 190, fee.title)
    c.drawString(220, height - 215, f"${fee.amount:,.2f}")
    c.drawString(220, height - 240, f"${fee.penalty_amount:,.2f}")
    c.drawString(220, height - 265, f"${fee.amount + fee.penalty_amount:,.2f}")
    c.drawString(220, height - 290, fee.payment_date.strftime('%Y-%m-%d'))
    c.drawString(220, height - 315, fee.status)

    # Footer
    c.setFillColor(colors.HexColor('#3da5d9'))
    c.setFont('Helvetica-Oblique', 9)
    c.drawString(50, 50, 'Thank you for using University Fee Management. Please keep this receipt for your records.')

    c.save()
    receipt = Receipt(fee_id=fee.id, receipt_file_path=filepath)
    db.session.add(receipt)
    db.session.commit()

@student_bp.route('/download_receipt/<int:fee_id>')
@login_required
def download_receipt(fee_id):
    if current_user.role != 'student':
        return redirect(url_for('home'))
    fee = Fee.query.get_or_404(fee_id)
    if fee.student_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('student.dashboard'))
    receipt = Receipt.query.filter_by(fee_id=fee_id).first()
    if receipt:
        return send_file(receipt.receipt_file_path, as_attachment=True)
    flash('Receipt not found', 'danger')
    return redirect(url_for('student.dashboard'))