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

def create_payos_signature(data, checksum_key):
    """Create PayOS signature theo format chính thức"""
    # Tạo chuỗi data để ký theo thứ tự alphabet
    sorted_keys = sorted(data.keys())
    query_string = '&'.join([f"{key}={data[key]}" for key in sorted_keys])
    
    # Tạo signature bằng HMAC SHA256
    signature = hmac.new(
        checksum_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

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
    current_app.logger.info(f'=== CREATE PAYMENT START ===')
    current_app.logger.info(f'User: {current_user.email}')
    current_app.logger.info(f'User verified: {current_user.is_verified}')
    current_app.logger.info(f'User paid: {current_user.has_paid}')
    
    if not current_user.is_verified:
        current_app.logger.error('User not verified')
        flash('Bạn cần xác thực email trước khi thanh toán', 'error')
        return redirect(url_for('main.dashboard'))
    
    if current_user.has_paid:
        current_app.logger.error('User already paid')
        flash('Bạn đã thanh toán rồi', 'info')
        return redirect(url_for('main.dashboard'))
    
    try:
        current_app.logger.info('Getting PayOS configuration...')
        # PayOS configuration
        client_id = current_app.config.get('PAYOS_CLIENT_ID')
        api_key = current_app.config.get('PAYOS_API_KEY')
        checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
        
        current_app.logger.info(f'Client ID: {client_id}')
        current_app.logger.info(f'API Key: {api_key[:10] if api_key else "None"}...')
        current_app.logger.info(f'Checksum Key: {checksum_key[:10] if checksum_key else "None"}...')
        
        if not all([client_id, api_key, checksum_key]):
            current_app.logger.error('PayOS configuration incomplete')
            flash('Cấu hình PayOS không đầy đủ', 'error')
            return redirect(url_for('payment.checkout'))
        
        current_app.logger.info('Creating payment data...')
        # Payment details
        amount = current_app.config.get('PAYMENT_AMOUNT', 50000)  # 50,000 VND
        order_code = int(f"{current_user.id}{int(datetime.now().timestamp())}")
        
        current_app.logger.info(f'Amount: {amount}')
        current_app.logger.info(f'Order code: {order_code}')
          # PayOS payment data theo API documentation có signature
        signature_data = {
            "amount": amount,
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "description": "MyApp Desktop",  # Giới hạn 25 ký tự cho PayOS
            "orderCode": order_code,
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL')
        }
        
        current_app.logger.info(f'Signature data: {signature_data}')
        
        # Tạo signature
        signature = create_payos_signature(signature_data, checksum_key)
        current_app.logger.info(f'Generated signature: {signature}')
        
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": "MyApp Desktop",  # Giới hạn 25 ký tự cho PayOS
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL'),
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "signature": signature
        }
        
        # Debug: In ra thông tin trước khi gọi API
        current_app.logger.info(f'PayOS payment data: {json.dumps(payment_data, indent=2)}')
        
        # Make request to PayOS API
        headers = {
            'x-client-id': client_id,
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        current_app.logger.info(f'Headers: {headers}')
        current_app.logger.info(f'Making request to PayOS API endpoint...')
        
        response = requests.post(
            'https://api-merchant.payos.vn/v2/payment-requests',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        current_app.logger.info(f'PayOS Response Status: {response.status_code}')
        current_app.logger.info(f'PayOS Response: {response.text}')
        
        if response.status_code == 200:
            result = response.json()
            current_app.logger.info(f'PayOS Result: {result}')
            
            if result.get('code') == '00' and result.get('data', {}).get('checkoutUrl'):
                current_app.logger.info('PayOS success, creating payment record...')
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
                current_app.logger.info('Payment record created successfully')
                
                checkout_url = result['data']['checkoutUrl']
                current_app.logger.info(f'Redirecting to checkout URL: {checkout_url}')
                # Redirect to PayOS payment page
                return redirect(checkout_url)
            else:
                error_msg = result.get('desc', 'Unknown error')
                current_app.logger.error(f'PayOS API returned error: {error_msg}')
                flash(f'PayOS Error: {error_msg}', 'error')
        else:
            current_app.logger.error(f'PayOS HTTP error: {response.status_code} - {response.text}')
            flash(f'Lỗi kết nối PayOS (Status: {response.status_code})', 'error')
        
        return redirect(url_for('payment.checkout'))
            
    except requests.RequestException as e:
        current_app.logger.error(f'PayOS request error: {str(e)}', exc_info=True)
        flash('Lỗi kết nối với PayOS. Vui lòng kiểm tra internet và thử lại.', 'error')
        return redirect(url_for('payment.checkout'))
    except Exception as e:
        current_app.logger.error(f'PayOS payment creation error: {str(e)}', exc_info=True)
        flash('Có lỗi xảy ra khi tạo thanh toán. Vui lòng thử lại.', 'error')
        return redirect(url_for('payment.checkout'))

@payment_bp.route('/return')
def payment_return():
    """Handle PayOS payment return"""
    try:
        current_app.logger.info('=== PAYMENT RETURN START ===')
        current_app.logger.info(f'All request args: {dict(request.args)}')
        
        # Get parameters from PayOS
        code = request.args.get('code')
        id = request.args.get('id')
        cancel = request.args.get('cancel')
        status = request.args.get('status')
        orderCode = request.args.get('orderCode')
        
        current_app.logger.info(f'PayOS return params:')
        current_app.logger.info(f'  - code: {code}')
        current_app.logger.info(f'  - id: {id}')
        current_app.logger.info(f'  - cancel: {cancel}')
        current_app.logger.info(f'  - status: {status}')
        current_app.logger.info(f'  - orderCode: {orderCode}')
        
        if not orderCode:
            current_app.logger.error('No orderCode found in return parameters')
            flash('Thiếu thông tin mã đơn hàng', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Find payment record
        payment = Payment.query.filter_by(payos_order_id=str(orderCode)).first()
        current_app.logger.info(f'Payment found: {payment is not None}')
        
        if not payment:
            current_app.logger.error(f'Payment not found for orderCode: {orderCode}')
            flash('Không tìm thấy thông tin thanh toán', 'error')
            return redirect(url_for('main.dashboard'))
        
        current_app.logger.info(f'Current payment status: {payment.status}')
        current_app.logger.info(f'Payment user ID: {payment.user_id}')
        
        if code == '00' and status == 'PAID':
            current_app.logger.info('Processing successful payment...')
            # Payment successful
            payment.status = 'PAID'
            payment.payos_transaction_id = id
            payment.completed_at = datetime.utcnow()
            
            # Update user payment status
            user = payment.user
            user.has_paid = True
            current_app.logger.info(f'Updated user {user.email} payment status to True')
            
            db.session.commit()
            current_app.logger.info('Payment and user status updated successfully')
            
            flash('Thanh toán thành công! Bạn có thể tải ứng dụng ngay bây giờ.', 'success')
        elif cancel == 'true':
            current_app.logger.info('Processing cancelled payment...')
            # Payment cancelled
            payment.status = 'CANCELLED'
            db.session.commit()
            flash('Thanh toán đã bị hủy', 'warning')
        else:
            current_app.logger.info('Processing failed payment...')
            # Payment failed
            payment.status = 'FAILED'
            db.session.commit()
            flash('Thanh toán thất bại. Vui lòng thử lại.', 'error')
    
    except Exception as e:
        current_app.logger.error(f'PayOS return error: {str(e)}', exc_info=True)
        flash('Có lỗi xảy ra khi xử lý kết quả thanh toán', 'error')
    
    current_app.logger.info('Redirecting to dashboard...')
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

@payment_bp.route('/test-payment', methods=['POST'])
@login_required  
def test_payment():
    """Test payment function đơn giản để debug"""
    current_app.logger.info('=== TEST PAYMENT FUNCTION ===')
    current_app.logger.info(f'User: {current_user.email}')
    current_app.logger.info(f'User ID: {current_user.id}')
    current_app.logger.info(f'Is verified: {current_user.is_verified}')
    current_app.logger.info(f'Has paid: {current_user.has_paid}')
    
    try:
        # Copy exact code từ test endpoint thành công
        client_id = current_app.config.get('PAYOS_CLIENT_ID')
        api_key = current_app.config.get('PAYOS_API_KEY')
        checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
        
        current_app.logger.info(f'Config check - Client ID: {bool(client_id)}')
        current_app.logger.info(f'Config check - API Key: {bool(api_key)}')
        current_app.logger.info(f'Config check - Checksum Key: {bool(checksum_key)}')
        
        if not all([client_id, api_key, checksum_key]):
            flash('PayOS configuration incomplete', 'error')
            return redirect(url_for('payment.checkout'))
        
        # Payment details
        amount = 50000
        order_code = int(datetime.now().timestamp())
        
        current_app.logger.info(f'Payment details - Amount: {amount}, Order: {order_code}')
          # PayOS payment data (copy từ test thành công)
        signature_data = {
            "amount": amount,
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "description": "Test payment",  # Giới hạn 25 ký tự
            "orderCode": order_code,
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL')
        }
        
        # Tạo signature
        signature = create_payos_signature(signature_data, checksum_key)
        current_app.logger.info(f'Generated signature: {signature}')
        
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": "Test payment",  # Giới hạn 25 ký tự
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL'),
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "signature": signature
        }
        
        current_app.logger.info(f'Payment data: {json.dumps(payment_data, indent=2)}')
        
        # Make request to PayOS API
        headers = {
            'x-client-id': client_id,
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        current_app.logger.info('Making PayOS request...')
        response = requests.post(
            'https://api-merchant.payos.vn/v2/payment-requests',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        current_app.logger.info(f'PayOS response status: {response.status_code}')
        current_app.logger.info(f'PayOS response: {response.text}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == '00' and result.get('data', {}).get('checkoutUrl'):
                current_app.logger.info(f'SUCCESS! Redirecting to: {result["data"]["checkoutUrl"]}')
                return redirect(result['data']['checkoutUrl'])
            else:
                error_msg = result.get('desc', 'Unknown error')
                current_app.logger.error(f'PayOS API error: {error_msg}')
                flash(f'PayOS Error: {error_msg}', 'error')
        else:
            current_app.logger.error(f'HTTP error: {response.status_code}')
            flash(f'HTTP Error: {response.status_code}', 'error')
        
        return redirect(url_for('payment.checkout'))
        
    except Exception as e:
        current_app.logger.error(f'Exception in test payment: {str(e)}', exc_info=True)
        flash(f'Exception: {str(e)}', 'error')
        return redirect(url_for('payment.checkout'))
