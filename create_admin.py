#!/usr/bin/env python3
"""
Script để tạo tài khoản admin và cập nhật database schema
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from config import Config

def create_admin_user():
    """Tạo tài khoản admin"""
    app = create_app()
    
    with app.app_context():
        # Kiểm tra xem admin đã tồn tại chưa
        admin = User.query.filter_by(email='admin@gmail.com').first()
        
        if admin:
            print("Tài khoản admin đã tồn tại!")
            # Cập nhật quyền admin nếu chưa có
            if not admin.is_admin:
                admin.is_admin = True
                admin.is_verified = True  # Admin tự động được verify
                db.session.commit()
                print("Đã cập nhật quyền admin cho tài khoản admin@gmail.com")
            else:
                print("Tài khoản admin@gmail.com đã có quyền admin")
        else:
            # Tạo tài khoản admin mới
            admin = User(
                email='admin@gmail.com',
                is_admin=True,
                is_verified=True,  # Admin tự động được verify
                has_paid=True  # Admin có thể download
            )
            admin.set_password('Admin@123')
            
            db.session.add(admin)
            db.session.commit()
            print("Đã tạo tài khoản admin thành công!")
            print("Email: admin@gmail.com")
            print("Password: Admin@123")

def update_database_schema():
    """Cập nhật database schema"""
    app = create_app()
    
    with app.app_context():
        try:
            # Tạo bảng mới nếu chưa có
            db.create_all()
            print("Đã cập nhật database schema thành công!")
        except Exception as e:
            print(f"Lỗi khi cập nhật database: {e}")

if __name__ == '__main__':
    print("=== Cập nhật Database và Tạo Admin ===")
    
    # 1. Cập nhật schema
    update_database_schema()
    
    # 2. Tạo admin user
    create_admin_user()
    
    print("=== Hoàn tất! ===")
