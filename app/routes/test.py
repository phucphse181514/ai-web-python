from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
import hashlib
import hmac
import json
import requests
from datetime import datetime

# Tạo blueprint test
test_bp = Blueprint('test', __name__, url_prefix='/test')

def create_payos_signature(data, checksum_key):
    """Create PayOS signature"""
    sorted_keys = sorted(data.keys())
    query_string = '&'.join([f"{key}={data[key]}" for key in sorted_keys])
    signature = hmac.new(
        checksum_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

@test_bp.route('/payos')
def test_payos():
    """Test PayOS API trực tiếp từ Flask"""
    try:
        # PayOS configuration
        client_id = current_app.config.get('PAYOS_CLIENT_ID')
        api_key = current_app.config.get('PAYOS_API_KEY')
        checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
        
        if not all([client_id, api_key, checksum_key]):
            return jsonify({'error': 'PayOS configuration incomplete'}), 400
        
        # Payment details
        amount = 50000
        order_code = int(datetime.now().timestamp())
          # PayOS payment data
        signature_data = {
            "amount": amount,
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "description": "Test Flask",  # Giới hạn 25 ký tự
            "orderCode": order_code,
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL')
        }
        
        # Tạo signature
        signature = create_payos_signature(signature_data, checksum_key)
        
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": "Test Flask",  # Giới hạn 25 ký tự
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL'),
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "signature": signature
        }
        
        # Make request to PayOS API
        headers = {
            'x-client-id': client_id,
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://api-merchant.payos.vn/v2/payment-requests',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == '00' and result.get('data', {}).get('checkoutUrl'):
                # Redirect to PayOS checkout page
                return redirect(result['data']['checkoutUrl'])
            else:
                return jsonify({
                    'error': 'PayOS Error',
                    'message': result.get('desc', 'Unknown error'),
                    'result': result
                }), 400
        else:
            return jsonify({
                'error': f'HTTP Error {response.status_code}',
                'response': response.text
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Exception: {str(e)}'}), 500

@test_bp.route('/user-status')
def user_status():
    """Check current user status for debugging"""
    from flask_login import current_user
    from app.models import User
    
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'email': current_user.email,
            'is_verified': current_user.is_verified,
            'has_paid': current_user.has_paid,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None
        })
    else:
        return jsonify({
            'authenticated': False,
            'message': 'User not logged in'
        })

@test_bp.route('/verify-user/<int:user_id>')
def verify_user(user_id):
    """Force verify a user for testing"""
    from app.models import User
    from app import db
    
    user = User.query.get(user_id)
    if user:
        user.is_verified = True
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'User {user.email} verified successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404

@test_bp.route('/payos-direct', methods=['GET', 'POST'])
def payos_direct():
    """Test PayOS trực tiếp với HTML form đơn giản"""
    if request.method == 'GET':
        # Hiển thị form test
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test PayOS Direct</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; }
                .form-group { margin: 20px 0; }
                button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; }
                .result { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h2>Test PayOS Direct</h2>
            <form method="POST">
                <div class="form-group">
                    <label>Amount (VND):</label>
                    <input type="number" name="amount" value="50000" required>
                </div>                <div class="form-group">
                    <label>Description (max 25 chars):</label>
                    <input type="text" name="description" value="Test payment" maxlength="25" required>
                </div>
                <button type="submit">Create PayOS Payment</button>
            </form>
        </body>
        </html>
        '''
    
    # POST request - tạo thanh toán
    try:
        amount = int(request.form.get('amount', 50000))
        description = request.form.get('description', 'Test payment')
        
        # PayOS configuration
        client_id = current_app.config.get('PAYOS_CLIENT_ID')
        api_key = current_app.config.get('PAYOS_API_KEY')
        checksum_key = current_app.config.get('PAYOS_CHECKSUM_KEY')
        
        if not all([client_id, api_key, checksum_key]):
            return jsonify({'error': 'PayOS configuration incomplete'}), 400
        
        # Payment details
        order_code = int(datetime.now().timestamp())
          # PayOS payment data
        signature_data = {
            "amount": amount,
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "description": description[:25],  # Giới hạn 25 ký tự
            "orderCode": order_code,
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL')
        }
        
        # Tạo signature
        signature = create_payos_signature(signature_data, checksum_key)
        
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": description[:25],  # Giới hạn 25 ký tự
            "returnUrl": current_app.config.get('PAYOS_RETURN_URL'),
            "cancelUrl": current_app.config.get('PAYOS_CANCEL_URL'),
            "signature": signature
        }
        
        # Make request to PayOS API
        headers = {
            'x-client-id': client_id,
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://api-merchant.payos.vn/v2/payment-requests',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == '00' and result.get('data', {}).get('checkoutUrl'):
                # Redirect to PayOS checkout page
                return redirect(result['data']['checkoutUrl'])
            else:
                return f'''
                <h2>PayOS Error</h2>
                <p>Error: {result.get('desc', 'Unknown error')}</p>
                <pre>{json.dumps(result, indent=2)}</pre>
                <a href="/test/payos-direct">Try Again</a>
                '''
        else:
            return f'''
            <h2>HTTP Error</h2>
            <p>Status: {response.status_code}</p>
            <pre>{response.text}</pre>
            <a href="/test/payos-direct">Try Again</a>
            '''
            
    except Exception as e:
        return f'''
        <h2>Exception Error</h2>
        <p>Error: {str(e)}</p>
        <a href="/test/payos-direct">Try Again</a>
        '''

@test_bp.route('/mark-payment-success/<int:user_id>')
def mark_payment_success(user_id):
    """Manually mark user payment as successful for testing"""
    from app.models import User, Payment
    from app import db
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Find latest payment for user
    payment = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).first()
    
    if payment:
        payment.status = 'PAID'
        payment.payos_transaction_id = f'test_txn_{int(datetime.now().timestamp())}'
        payment.completed_at = datetime.utcnow()
    
    # Update user payment status
    user.has_paid = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {user.email} payment marked as successful',
        'payment_id': payment.id if payment else None,
        'user_has_paid': user.has_paid
    })

@test_bp.route('/check-payment-status/<int:user_id>')
def check_payment_status(user_id):
    """Check user payment status and sync if needed"""
    from app.models import User, Payment
    from app import db
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get all payments for user
    payments = Payment.query.filter_by(user_id=user_id).all()
    paid_payments = [p for p in payments if p.status == 'PAID']
    
    # Check if user should have paid status
    should_be_paid = len(paid_payments) > 0
    
    # Sync user status if needed
    if should_be_paid and not user.has_paid:
        user.has_paid = True
        db.session.commit()
        sync_message = "User payment status synced to PAID"
    elif not should_be_paid and user.has_paid:
        user.has_paid = False
        db.session.commit()
        sync_message = "User payment status synced to NOT PAID"
    else:
        sync_message = "User payment status is already correct"
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'user_email': user.email,
        'user_has_paid': user.has_paid,
        'total_payments': len(payments),
        'paid_payments': len(paid_payments),
        'should_be_paid': should_be_paid,
        'sync_message': sync_message,
        'payment_details': [
            {
                'id': p.id,
                'payos_order_id': p.payos_order_id,
                'amount': p.amount,
                'status': p.status,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'completed_at': p.completed_at.isoformat() if p.completed_at else None
            } for p in payments
        ]
    })

@test_bp.route('/sync-all-users-payment-status')
def sync_all_users_payment_status():
    """Sync payment status for all users based on their payment records"""
    from app.models import User, Payment
    from app import db
    
    users = User.query.all()
    synced_users = []
    
    for user in users:
        paid_payments = Payment.query.filter_by(user_id=user.id, status='PAID').count()
        should_be_paid = paid_payments > 0
        
        if user.has_paid != should_be_paid:
            old_status = user.has_paid
            user.has_paid = should_be_paid
            synced_users.append({
                'user_id': user.id,
                'email': user.email,
                'old_status': old_status,
                'new_status': should_be_paid,
                'paid_payments_count': paid_payments
            })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Synced {len(synced_users)} users',
        'synced_users': synced_users,
        'total_users': len(users)
    })
