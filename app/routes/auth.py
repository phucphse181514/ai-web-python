from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from app import db, mail
from app.models import User
from datetime import datetime, timezone, timedelta
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_vietnam_time():
    """Get current time in Vietnam timezone (UTC+7)"""
    vietnam_tz = timezone(timedelta(hours=7))
    vietnam_time = datetime.now(vietnam_tz)
    return vietnam_time.strftime('%d/%m/%Y lúc %H:%M:%S (UTC+7)')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"
    if not re.search(r'[A-Z]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
    if not re.search(r'[a-z]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường"
    if not re.search(r'[0-9]', password):
        return False, "Mật khẩu phải có ít nhất 1 số"
    return True, "Mật khẩu hợp lệ"

def send_verification_email(user):
    """Send email verification"""
    token = user.generate_verification_token()
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    current_time_vn = get_vietnam_time()
    
    msg = Message(
        subject='Xác thực tài khoản Mahika của bạn',
        recipients=[user.email],
        html=render_template('emails/verification.html', 
                           user=user, 
                           verification_url=verification_url,
                           current_time_vn=current_time_vn),
        body=f'Vui lòng truy cập liên kết sau để xác thực tài khoản: {verification_url}'
    )
    mail.send(msg)

def send_reset_email(user):
    """Send password reset email"""
    token = user.generate_reset_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    current_time_vn = get_vietnam_time()
    
    msg = Message(
        subject='Đặt lại mật khẩu Mahika',
        recipients=[user.email],
        html=render_template('emails/reset_password.html', 
                           user=user, 
                           reset_url=reset_url,
                           current_time_vn=current_time_vn),
        body=f'Vui lòng truy cập liên kết sau để đặt lại mật khẩu: {reset_url}'
    )
    mail.send(msg)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not email or not password:
            flash('Vui lòng điền đầy đủ thông tin', 'error')
            return render_template('auth/register.html')
        
        if not validate_email(email):
            flash('Email không hợp lệ', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('auth/register.html')
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email này đã được đăng ký', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            send_verification_email(user)
            
            flash('Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra khi đăng ký. Vui lòng thử lại.', 'error')
            current_app.logger.error(f'Registration error: {str(e)}')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not email or not password:
            flash('Vui lòng điền đầy đủ thông tin', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email hoặc mật khẩu không đúng', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Đã đăng xuất thành công', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    user = User.verify_verification_token(token)
    if not user:
        flash('Link xác thực không hợp lệ hoặc đã hết hạn', 'error')
        return redirect(url_for('auth.login'))
    
    if user.is_verified:
        flash('Tài khoản đã được xác thực trước đó', 'info')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    user.verified_at = datetime.utcnow()
    db.session.commit()
    
    flash('Xác thực email thành công! Bạn có thể đăng nhập ngay bây giờ.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Vui lòng nhập email', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_email(user)
        
        # Always show success message for security
        flash('Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or not confirm_password:
            flash('Vui lòng điền đầy đủ thông tin', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/reset_password.html', token=token)
        
        user.set_password(password)
        db.session.commit()
        
        flash('Đặt lại mật khẩu thành công! Bạn có thể đăng nhập với mật khẩu mới.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    """Resend verification email"""
    if current_user.is_verified:
        flash('Tài khoản đã được xác thực', 'info')
        return redirect(url_for('main.dashboard'))
    
    send_verification_email(current_user)
    flash('Email xác thực đã được gửi lại', 'success')
    return redirect(url_for('main.dashboard'))
