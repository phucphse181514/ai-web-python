#!/usr/bin/env python3
"""
Script test kết nối Railway MySQL database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_railway_connection():
    """Test Railway database connection"""
    
    print("=== Railway Database Connection Test ===")
    
    # Check environment variables
    database_url = os.getenv('DATABASE_URL')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    
    print(f"DATABASE_URL: {'✓' if database_url else '✗'}")
    print(f"DB_HOST: {db_host}")
    print(f"DB_PORT: {db_port}")
    print(f"DB_NAME: {db_name}")
    print(f"DB_USER: {db_user}")
    print(f"DB_PASSWORD: {'✓' if db_password else '✗'}")
    
    if not any([database_url, all([db_host, db_user, db_password])]):
        print("❌ Missing database configuration!")
        print("Please set either DATABASE_URL or individual DB_* variables")
        return False
    
    try:
        print("\n=== Testing Flask App Connection ===")
        
        from app import create_app, db
        from app.models import User, Payment
        
        app = create_app()
        
        with app.app_context():
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Test basic connection
            print("Testing database connection...")
            result = db.engine.execute("SELECT 1 as test").fetchone()
            print(f"✅ Connection successful! Test query result: {result[0]}")
            
            # Test table creation
            print("Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Test table existence
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Found tables: {tables}")
            
            # Test basic queries
            users = User.query.all()
            payments = Payment.query.all()
            print(f"✅ Found {len(users)} users and {len(payments)} payments")
            
            # Test insert (create a test user if none exists)
            if len(users) == 0:
                print("Creating test user...")
                test_user = User(
                    email='test@railway.app',
                    password='hashed_password_here',
                    is_verified=True
                )
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created successfully!")
            
            print("\n🎉 Railway database is working perfectly!")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_railway_setup_instructions():
    """Print Railway setup instructions"""
    
    print("\n" + "="*60)
    print("🚀 RAILWAY MYSQL SETUP INSTRUCTIONS")
    print("="*60)
    
    print("""
1. Go to https://railway.app/
2. Sign up with GitHub account
3. Click "Start a New Project"
4. Select "Provision MySQL"
5. Wait for database to be created
6. Go to your project dashboard
7. Click on MySQL service
8. Go to "Variables" or "Connect" tab
9. Copy the connection details

Add to your .env file:
""")
    
    print("""
# Railway MySQL Configuration
DATABASE_URL=mysql://root:password@containers-us-west-xxx.railway.app:7xxx/railway

# Or individual variables:
DB_HOST=containers-us-west-xxx.railway.app
DB_PORT=7xxx
DB_NAME=railway
DB_USER=root
DB_PASSWORD=your_railway_password
""")
    
    print("""
Then run this script again to test the connection:
python test_railway_connection.py
""")

if __name__ == "__main__":
    success = test_railway_connection()
    
    if not success:
        get_railway_setup_instructions()
    else:
        print("\n✅ Your Railway database is ready for production!")
        print("✅ Team members can now use the same database")
        print("✅ PayOS payments will be saved to Railway MySQL")
        
        print("\nNext steps:")
        print("1. Share the DATABASE_URL with your team")
        print("2. Update PayOS return URLs if needed")
        print("3. Test the full payment flow")
