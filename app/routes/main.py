from flask import Blueprint, render_template, send_file, flash, redirect, url_for, current_app, abort, Response
from flask_login import login_required, current_user
import os
import requests
import tempfile
import time

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
      # Check if using Google Drive URL
    if current_app.config.get('DOWNLOAD_FILE_URL'):
        try:
            # Download file from Google Drive and serve it directly
            response = requests.get(current_app.config['DOWNLOAD_FILE_URL'], stream=True)
            response.raise_for_status()
            
            # Create a generator to stream the file
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Return the file as a download
            return Response(
                generate(),
                headers={
                    'Content-Disposition': f'attachment; filename="{current_app.config["DOWNLOAD_FILE_NAME"]}"',
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': response.headers.get('Content-Length', '')
                }
            )
            
        except requests.RequestException as e:
            current_app.logger.error(f'Google Drive download error: {str(e)}')
            flash('Không thể tải file từ Google Drive. Vui lòng thử lại sau.', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Fallback to local file
    file_path = os.path.join(current_app.root_path, current_app.config['DOWNLOAD_FILE_PATH'])
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

@main_bp.route('/download-direct')
@login_required
def download_direct():
    """Direct download without showing Google Drive page"""
    # Check if user is verified and has paid
    if not current_user.is_verified:
        flash('Bạn cần xác thực email trước khi tải ứng dụng', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if not current_user.has_paid:
        flash('Bạn cần thanh toán trước khi tải ứng dụng', 'warning')
        return redirect(url_for('payment.checkout'))
    
    # Check if using Google Drive URL
    if current_app.config.get('DOWNLOAD_FILE_URL'):
        try:
            # Create cache directory if not exists
            cache_dir = os.path.join(current_app.root_path, 'static', 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            cached_file = os.path.join(cache_dir, current_app.config['DOWNLOAD_FILE_NAME'])
            
            # Check if file is already cached (và không quá cũ - 1 giờ)
            if os.path.exists(cached_file):
                file_age = time.time() - os.path.getmtime(cached_file)
                if file_age < 3600:  # 1 hour
                    current_app.logger.info(f'Serving cached file for user {current_user.email}')
                    return send_file(
                        cached_file,
                        as_attachment=True,
                        download_name=current_app.config['DOWNLOAD_FILE_NAME'],
                        mimetype='application/octet-stream'
                    )
            
            # Download from Google Drive to cache
            current_app.logger.info(f'Downloading fresh file from Google Drive for user {current_user.email}')
            response = requests.get(current_app.config['DOWNLOAD_FILE_URL'], stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            with open(cached_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Serve the cached file
            return send_file(
                cached_file,
                as_attachment=True,
                download_name=current_app.config['DOWNLOAD_FILE_NAME'],
                mimetype='application/octet-stream'
            )
            
        except Exception as e:
            current_app.logger.error(f'Direct download error: {str(e)}')
            flash('Không thể tải file. Vui lòng thử lại sau.', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Fallback to regular download
    return redirect(url_for('main.download'))
