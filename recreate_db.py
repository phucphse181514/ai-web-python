#!/usr/bin/env python3
"""
Script để recreate database với PayOS schema
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Payment

def recreate_database():
    """Recreate database with new PayOS schema"""
    
    print("Creating Flask app...")
    app = create_app()
    
    with app.app_context():
        print("Dropping all existing tables...")
        db.drop_all()
        
        print("Creating new tables with PayOS schema...")
        db.create_all()
        
        print("Database schema recreation completed successfully!")
        
        # Verify tables
        print("\nVerifying tables...")
        print(f"Users table: {db.engine.dialect.has_table(db.engine.connect(), 'users')}")
        print(f"Payments table: {db.engine.dialect.has_table(db.engine.connect(), 'payments')}")
        
        # Show Payment table columns
        inspector = db.inspect(db.engine)
        payment_columns = inspector.get_columns('payments')
        print(f"\nPayment table columns:")
        for col in payment_columns:
            print(f"  - {col['name']}: {col['type']}")

if __name__ == "__main__":
    recreate_database()
