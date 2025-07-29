from flask import Blueprint, render_template, send_file, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html', user=current_user)

@main_bp.route('/download')
@login_required
def download():
    """Download the application file"""
    # Check if user is verified and has paid
    if not current_user.is_verified:
        flash('Bạn cần xác thực email trước khi tải ứng dụng', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if not current_user.has_paid:
        flash('Bạn cần thanh toán trước khi tải ứng dụng', 'warning')
        return redirect(url_for('payment.checkout'))
    
    # Check if file exists
    file_path = os.path.join(current_app.root_path, '..', current_app.config['DOWNLOAD_FILE_PATH'])
    if not os.path.exists(file_path):
        current_app.logger.error(f'Download file not found: {file_path}')
        flash('File ứng dụng hiện không khả dụng. Vui lòng liên hệ hỗ trợ.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=current_app.config['DOWNLOAD_FILE_NAME'],
            mimetype='application/octet-stream'
        )
    except Exception as e:
        current_app.logger.error(f'Download error: {str(e)}')
        flash('Có lỗi khi tải file. Vui lòng thử lại sau.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@main_bp.route('/support')
def support():
    """Support page"""
    return render_template('support.html')

@main_bp.route('/terms')
def terms():
    """Terms of service"""
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')
