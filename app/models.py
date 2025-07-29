from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    has_paid = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationship
    payments = db.relationship('Payment', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        """Generate email verification token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='email-verification')
    
    def generate_reset_token(self):
        """Generate password reset token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='password-reset')
    
    @staticmethod
    def verify_verification_token(token, max_age=3600):
        """Verify email verification token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='email-verification', max_age=max_age)
            return User.query.filter_by(email=email).first()
        except:
            return None
    
    @staticmethod
    def verify_reset_token(token, max_age=3600):
        """Verify password reset token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset', max_age=max_age)
            return User.query.filter_by(email=email).first()
        except:
            return None
    
    def can_download(self):
        """Check if user can download the app"""
        return self.is_verified and self.has_paid
    
    def __repr__(self):
        return f'<User {self.email}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payos_order_id = db.Column(db.String(255), unique=True, nullable=False)
    payos_transaction_id = db.Column(db.String(255), unique=True, nullable=True)
    amount = db.Column(db.Integer, nullable=False)  # Amount in VND
    currency = db.Column(db.String(3), default='VND', nullable=False)
    status = db.Column(db.String(50), nullable=False)  # PAID, PENDING, CANCELLED, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Payment {self.payos_order_id}: {self.status}>'
