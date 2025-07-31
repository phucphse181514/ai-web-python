#!/usr/bin/env python3
"""
Script để tạo password hash cho admin
"""
from werkzeug.security import generate_password_hash

# Tạo hash cho mật khẩu Admin@123
password = 'Admin@123'
password_hash = generate_password_hash(password)

print("=== Password Hash cho Admin@123 ===")
print(f"Password: {password}")
print(f"Hash: {password_hash}")
print()
print("SQL để tạo admin:")
print(f"""
INSERT INTO users (email, password_hash, is_verified, has_paid, is_admin, created_at) 
VALUES (
    'admin@gmail.com',
    '{password_hash}',
    1,
    1,
    1,
    NOW()
);
""")
print()
print("Hoặc SQL để cập nhật admin hiện có:")
print(f"""
UPDATE users 
SET password_hash = '{password_hash}', is_admin = 1, is_verified = 1, has_paid = 1 
WHERE email = 'admin@gmail.com';
""")
