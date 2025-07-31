#!/usr/bin/env python3
"""
Script để thêm cột is_admin vào bảng users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from config import Config

def add_is_admin_column():
    """Thêm cột is_admin vào bảng users"""
    app = create_app()
    
    with app.app_context():
        try:
            # Kiểm tra xem cột đã tồn tại chưa
            result = db.engine.execute("SHOW COLUMNS FROM users LIKE 'is_admin'")
            if result.fetchone():
                print("Cột is_admin đã tồn tại!")
                return True
            
            # Thêm cột is_admin
            db.engine.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE")
            print("Đã thêm cột is_admin vào bảng users thành công!")
            return True
            
        except Exception as e:
            print(f"Lỗi khi thêm cột is_admin: {e}")
            return False

if __name__ == '__main__':
    print("=== Thêm cột is_admin vào bảng users ===")
    
    if add_is_admin_column():
        print("=== Migration hoàn tất! ===")
    else:
        print("=== Migration thất bại! ===")
        sys.exit(1)
