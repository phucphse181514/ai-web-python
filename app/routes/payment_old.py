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

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

def generate_payos_signature(data, checksum_key):
    """Generate PayOS signature"""
    # Sort data by key and create query string
    sorted_data = dict(sorted(data.items()))
    query_string = '&'.join([f"{k}={v}" for k, v in sorted_data.items()])
    
    # Generate HMAC SHA256 signature
    return hmac.new(
        checksum_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def create_payos_payment_request(order_code, amount, description, return_url, cancel_url):
    """Create PayOS payment request"""
    # PayOS configuration from environment
    client_id = current_app.config.get('PAYOS_CLIENT_ID')
    api_key = current_app.config.get('PAYOS_API_KEY')
    checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
    
    if not all([client_id, api_key, checksum_key]):
        raise ValueError("PayOS configuration is incomplete")
    
    # Request data
    data = {
        "orderCode": order_code,
        "amount": amount,
        "description": description,
        "returnUrl": return_url,
        "cancelUrl": cancel_url
    }
    
    # Generate signature
    signature = generate_payos_signature(data, checksum_key)
    
    # Headers
    headers = {
        'x-client-id': client_id,
        'x-api-key': api_key,
        'x-partner-code': current_app.config.get('PAYOS_PARTNER_CODE'),
        'Content-Type': 'application/json'
    }
    
    # Add signature to data
    data['signature'] = signature
    
    return data, headers

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
        description = f"Thanh toan ung dung - User {current_user.email}"
        
        # URLs
        return_url = url_for('payment.payment_return', _external=True)
        cancel_url = url_for('payment.cancel_payment', _external=True)
        
        # Create PayOS payment request
        payment_data, headers = create_payos_payment_request(
            order_code, amount, description, return_url, cancel_url
        )
        
        # Send request to PayOS
        endpoint = "https://api-merchant.payos.vn/v2/payment-requests"
        response = requests.post(endpoint, json=payment_data, headers=headers, timeout=30)
        result = response.json()
        
        if result.get('error') == 0:
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
            return redirect(result['data']['checkoutUrl'])
        else:
            flash(f'Lỗi tạo thanh toán: {result.get("desc", "Unknown error")}', 'error')
            return redirect(url_for('payment.checkout'))
            
    except Exception as e:
        current_app.logger.error(f'Payment creation error: {str(e)}')
        flash('Có lỗi xảy ra khi tạo thanh toán. Vui lòng thử lại.', 'error')
        return redirect(url_for('payment.checkout'))

@payment_bp.route('/return')
def payment_return():
    """Handle PayOS payment return"""
    # Get parameters from PayOS
    code = request.args.get('code')
    id = request.args.get('id')
    cancel = request.args.get('cancel')
    status = request.args.get('status')
    order_code = request.args.get('orderCode')
    
    if cancel == 'true':
        flash('Thanh toán đã bị hủy', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Find payment record
    payment = Payment.query.filter_by(payos_order_id=order_code).first()
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
    else:
        # Payment failed
        payment.status = 'CANCELLED'
        db.session.commit()
        
        flash('Thanh toán thất bại hoặc bị hủy', 'error')
    
    return redirect(url_for('main.dashboard'))

@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Handle PayOS webhook"""
    try:
        data = request.get_json()
        
        # Verify webhook signature
        checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
        webhook_signature = request.headers.get('x-payos-signature')
        
        # Create signature from data
        expected_signature = generate_payos_signature(data, checksum_key)
        
        if webhook_signature != expected_signature:
            current_app.logger.error('Invalid PayOS webhook signature')
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Process webhook data
        order_code = data.get('orderCode')
        status = data.get('status')
        transaction_id = data.get('id')
        
        # Find payment record
        payment = Payment.query.filter_by(payos_order_id=str(order_code)).first()
        if not payment:
            current_app.logger.error(f'Payment not found for order {order_code}')
            return jsonify({'error': 'Payment not found'}), 404
        
        if status == 'PAID':
            # Payment successful
            if payment.status != 'PAID':
                payment.status = 'PAID'
                payment.payos_transaction_id = transaction_id
                payment.completed_at = datetime.utcnow()
                
                # Update user payment status
                user = payment.user
                user.has_paid = True
                
                db.session.commit()
                
                current_app.logger.info(f'Payment completed for order {order_code}')
        elif status == 'CANCELLED':
            # Payment cancelled
            payment.status = 'CANCELLED'
            db.session.commit()
            
            current_app.logger.info(f'Payment cancelled for order {order_code}')
        
        return jsonify({'success': True}), 200
        
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
@login_required
def cancel_payment():
    """Cancel payment"""
    flash('Thanh toán đã bị hủy', 'info')
    return redirect(url_for('main.dashboard'))
