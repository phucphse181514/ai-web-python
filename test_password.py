#!/usr/bin/env python3
"""
Script để test password admin
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash, check_password_hash

# Test password
password = 'Admin@123'
hash1 = generate_password_hash(password)
hash2 = generate_password_hash(password)

print("=== Test Password Hash ===")
print(f"Password: {password}")
print(f"Hash 1: {hash1}")
print(f"Hash 2: {hash2}")
print()

# Test check password
print("=== Test Check Password ===")
print(f"Hash 1 matches password: {check_password_hash(hash1, password)}")
print(f"Hash 2 matches password: {check_password_hash(hash2, password)}")
print(f"Hash 1 matches wrong password: {check_password_hash(hash1, 'wrong')}")
print()

print("SQL để cập nhật admin:")
print(f"""
UPDATE users 
SET password_hash = '{hash1}'
WHERE email = 'admin@gmail.com';
""")
