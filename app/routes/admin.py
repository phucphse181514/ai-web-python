from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Payment
from datetime import datetime, timedelta
from sqlalchemy import func, extract

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator để kiểm tra quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang này.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Trang dashboard admin"""
    # Thống kê tổng quan
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    paid_users = User.query.filter_by(has_paid=True).count()
    total_payments = Payment.query.filter_by(status='PAID').count()
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(status='PAID').scalar() or 0
    
    # Thống kê hôm nay
    today = datetime.utcnow().date()
    today_users = User.query.filter(func.date(User.created_at) == today).count()
    today_payments = Payment.query.filter(
        func.date(Payment.completed_at) == today,
        Payment.status == 'PAID'
    ).count()
    today_revenue = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.completed_at) == today,
        Payment.status == 'PAID'
    ).scalar() or 0
    
    # Thống kê 30 ngày gần nhất
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    recent_payments = Payment.query.filter(
        Payment.completed_at >= thirty_days_ago,
        Payment.status == 'PAID'
    ).count()
    recent_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.completed_at >= thirty_days_ago,
        Payment.status == 'PAID'
    ).scalar() or 0
    
    stats = {
        'total_users': total_users,
        'verified_users': verified_users,
        'paid_users': paid_users,
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'today_users': today_users,
        'today_payments': today_payments,
        'today_revenue': today_revenue,
        'recent_users': recent_users,
        'recent_payments': recent_payments,
        'recent_revenue': recent_revenue
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Danh sách người dùng"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter options
    filter_verified = request.args.get('verified')
    filter_paid = request.args.get('paid')
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    # Apply filters
    if filter_verified == 'true':
        query = query.filter_by(is_verified=True)
    elif filter_verified == 'false':
        query = query.filter_by(is_verified=False)
        
    if filter_paid == 'true':
        query = query.filter_by(has_paid=True)
    elif filter_paid == 'false':
        query = query.filter_by(has_paid=False)
        
    if search:
        query = query.filter(User.email.contains(search))
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users, 
                         filter_verified=filter_verified, 
                         filter_paid=filter_paid, 
                         search=search)

@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Thống kê chi tiết"""
    # Thống kê theo tháng (12 tháng gần nhất)
    monthly_stats = []
    for i in range(12):
        date = datetime.utcnow() - timedelta(days=30 * i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            month_end = datetime.utcnow()
        else:
            next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
            month_end = next_month - timedelta(seconds=1)
        
        payments_count = Payment.query.filter(
            Payment.completed_at >= month_start,
            Payment.completed_at <= month_end,
            Payment.status == 'PAID'
        ).count()
        
        revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.completed_at >= month_start,
            Payment.completed_at <= month_end,
            Payment.status == 'PAID'
        ).scalar() or 0
        
        new_users = User.query.filter(
            User.created_at >= month_start,
            User.created_at <= month_end
        ).count()
        
        monthly_stats.append({
            'month': month_start.strftime('%m/%Y'),
            'payments_count': payments_count,
            'revenue': revenue,
            'new_users': new_users
        })
    
    monthly_stats.reverse()  # Hiển thị từ tháng cũ đến mới
    
    return render_template('admin/statistics.html', monthly_stats=monthly_stats)

@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    """Danh sách giao dịch"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter options
    filter_status = request.args.get('status')
    search = request.args.get('search', '').strip()
    
    query = Payment.query
    
    # Apply filters
    if filter_status:
        query = query.filter_by(status=filter_status)
        
    if search:
        # Search by order ID or user email
        query = query.join(User).filter(
            db.or_(
                Payment.payos_order_id.contains(search),
                User.email.contains(search)
            )
        )
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/payments.html', payments=payments,
                         filter_status=filter_status, search=search)

@admin_bp.route('/user/<int:user_id>/toggle-verified')
@login_required
@admin_required
def toggle_user_verified(user_id):
    """Chuyển đổi trạng thái xác thực của user"""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Không thể thay đổi trạng thái admin!', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_verified = not user.is_verified
    if user.is_verified:
        user.verified_at = datetime.utcnow()
    
    db.session.commit()
    status = 'đã xác thực' if user.is_verified else 'chưa xác thực'
    flash(f'Đã cập nhật trạng thái user {user.email} thành {status}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/<int:user_id>/toggle-paid')
@login_required
@admin_required
def toggle_user_paid(user_id):
    """Chuyển đổi trạng thái thanh toán của user"""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Không thể thay đổi trạng thái admin!', 'error')
        return redirect(url_for('admin.users'))
    
    user.has_paid = not user.has_paid
    db.session.commit()
    
    status = 'đã thanh toán' if user.has_paid else 'chưa thanh toán'
    flash(f'Đã cập nhật trạng thái user {user.email} thành {status}', 'success')
    return redirect(url_for('admin.users'))
