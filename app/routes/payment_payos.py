from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Payment
import hashlib
import hmac
import uuid
import json
import requests
from datetime import datetime
import os
from payos import PayOS, PaymentData, ItemData

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

def get_payos_client():
    """Initialize PayOS client"""
    client_id = current_app.config.get('PAYOS_CLIENT_ID')
    api_key = current_app.config.get('PAYOS_API_KEY')
    checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
    
    if not all([client_id, api_key, checksum_key]):
        raise ValueError("PayOS configuration is incomplete")
    
    return PayOS(client_id, api_key, checksum_key)

@payment_bp.route('/checkout')
@login_required
def checkout():
    """Display checkout page"""
    if not current_user.is_verified:
        flash('Bạn cần xác thực email trước khi thanh toán', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if current_user.has_paid:
        flash('Bạn đã thanh toán rồi', 'info')
        return redirect(url_for('main.dashboard'))
    
    return render_template('payment/checkout.html')

@payment_bp.route('/create-payment', methods=['POST'])
@login_required
def create_payment():
    """Create PayOS payment"""
    if not current_user.is_verified:
        flash('Bạn cần xác thực email trước khi thanh toán', 'error')
        return redirect(url_for('main.dashboard'))
    
    if current_user.has_paid:
        flash('Bạn đã thanh toán rồi', 'info')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Payment details
        amount = current_app.config.get('PAYMENT_AMOUNT', 50000)  # 50,000 VND
        order_code = int(f"{current_user.id}{int(datetime.now().timestamp())}")
        
        # PayOS payment data
        item_data = ItemData(
            name="MyApp - Ứng dụng Desktop",
            quantity=1,
            price=amount
        )
        
        payment_data = PaymentData(
            orderCode=order_code,
            amount=amount,
            description=f"Thanh toán ứng dụng MyApp - User {current_user.email}",
            items=[item_data],
            returnUrl=current_app.config.get('PAYOS_RETURN_URL'),
            cancelUrl=current_app.config.get('PAYOS_CANCEL_URL')
        )
        
        # Create PayOS client and payment link
        payos = get_payos_client()
        response = payos.createPaymentLink(payment_data)
        
        if response and response.get('checkoutUrl'):
            # Create payment record in database
            payment = Payment(
                user_id=current_user.id,
                payos_order_id=str(order_code),
                amount=amount,
                currency='VND',
                status='PENDING'
            )
            db.session.add(payment)
            db.session.commit()
            
            # Redirect to PayOS payment page
            return redirect(response['checkoutUrl'])
        else:
            flash('Không thể tạo liên kết thanh toán. Vui lòng thử lại.', 'error')
            return redirect(url_for('payment.checkout'))
            
    except Exception as e:
        current_app.logger.error(f'PayOS payment creation error: {str(e)}')
        flash('Có lỗi xảy ra khi tạo thanh toán. Vui lòng thử lại.', 'error')
        return redirect(url_for('payment.checkout'))

@payment_bp.route('/return')
def payment_return():
    """Handle PayOS payment return"""
    try:
        # Get parameters from PayOS
        code = request.args.get('code')
        id = request.args.get('id')
        cancel = request.args.get('cancel')
        status = request.args.get('status')
        orderCode = request.args.get('orderCode')
        
        # Find payment record
        payment = Payment.query.filter_by(payos_order_id=orderCode).first()
        if not payment:
            flash('Không tìm thấy thông tin thanh toán', 'error')
            return redirect(url_for('main.dashboard'))
        
        if code == '00' and status == 'PAID':
            # Payment successful
            payment.status = 'PAID'
            payment.payos_transaction_id = id
            payment.completed_at = datetime.utcnow()
            
            # Update user payment status
            user = payment.user
            user.has_paid = True
            
            db.session.commit()
            
            flash('Thanh toán thành công! Bạn có thể tải ứng dụng ngay bây giờ.', 'success')
        elif cancel == 'true':
            # Payment cancelled
            payment.status = 'CANCELLED'
            db.session.commit()
            flash('Thanh toán đã bị hủy', 'warning')
        else:
            # Payment failed
            payment.status = 'FAILED'
            db.session.commit()
            flash('Thanh toán thất bại. Vui lòng thử lại.', 'error')
    
    except Exception as e:
        current_app.logger.error(f'PayOS return error: {str(e)}')
        flash('Có lỗi xảy ra khi xử lý kết quả thanh toán', 'error')
    
    return redirect(url_for('main.dashboard'))

@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Handle PayOS webhook notification"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract webhook data
        webhook_data = data.get('data', {})
        order_code = webhook_data.get('orderCode')
        amount = webhook_data.get('amount')
        description = webhook_data.get('description')
        account_number = webhook_data.get('accountNumber')
        reference = webhook_data.get('reference')
        transaction_date_time = webhook_data.get('transactionDateTime')
        
        # Find payment record
        payment = Payment.query.filter_by(payos_order_id=str(order_code)).first()
        if not payment:
            current_app.logger.error(f'Payment not found for order {order_code}')
            return jsonify({'error': 'Payment not found'}), 404
        
        # Update payment status
        if amount == payment.amount and payment.status == 'PENDING':
            payment.status = 'PAID'
            payment.payos_transaction_id = reference
            payment.completed_at = datetime.utcnow()
            
            # Update user payment status
            user = payment.user
            user.has_paid = True
            
            db.session.commit()
            
            current_app.logger.info(f'Payment completed via webhook for order {order_code}')
        
        return jsonify({'code': '00', 'desc': 'Success'}), 200
        
    except Exception as e:
        current_app.logger.error(f'PayOS webhook error: {str(e)}')
        return jsonify({'error': 'Internal error'}), 500

@payment_bp.route('/history')
@login_required
def payment_history():
    """Display user's payment history"""
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    return render_template('payment/history.html', payments=payments)

@payment_bp.route('/cancel')
def cancel_payment():
    """Cancel payment"""
    flash('Thanh toán đã bị hủy', 'info')
    return redirect(url_for('main.dashboard'))
