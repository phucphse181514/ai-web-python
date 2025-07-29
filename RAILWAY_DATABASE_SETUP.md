# Railway MySQL Database Setup Guide

## 1. Deploy MySQL trên Railway

### Tạo dự án mới:

1. Đăng nhập [Railway.app](https://railway.app/)
2. Click "Start a New Project"
3. Chọn "Provision MySQL"
4. Đợi database được khởi tạo

### Lấy thông tin kết nối:

1. Vào project dashboard
2. Click vào MySQL service
3. Vào tab "Variables" hoặc "Connect"
4. Copy các thông tin sau:

```env
MYSQL_HOST=containers-us-west-xxx.railway.app
MYSQL_PORT=7xxx
MYSQL_USER=root
MYSQL_PASSWORD=xxxxxxxxxxxx
MYSQL_DATABASE=railway
DATABASE_URL=mysql://root:password@host:port/railway
```

## 2. Cập nhật file .env

Thay thế cấu hình database local bằng Railway:

```env
# Railway Database Configuration
DB_HOST=containers-us-west-xxx.railway.app
DB_PORT=7xxx
DB_NAME=railway
DB_USER=root
DB_PASSWORD=your_railway_password
```

## 3. Cập nhật config.py

Thêm support cho Railway database URL:

```python
import os
from urllib.parse import urlparse

class Config:
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        # Parse Railway DATABASE_URL
        url = urlparse(DATABASE_URL)
        DB_HOST = url.hostname
        DB_PORT = url.port
        DB_NAME = url.path[1:]  # Remove leading slash
        DB_USER = url.username
        DB_PASSWORD = url.password
    else:
        # Fallback to individual env vars
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', 3306)
        DB_NAME = os.getenv('DB_NAME', 'flask_app')
        DB_USER = os.getenv('DB_USER', 'root')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
```

## 4. Test kết nối

Chạy script test để verify kết nối:

```python
# test_railway_connection.py
from app import create_app, db
from app.models import User, Payment

app = create_app()
with app.app_context():
    try:
        # Test connection
        db.engine.execute('SELECT 1')
        print("✅ Railway database connection successful!")

        # Create tables
        db.create_all()
        print("✅ Tables created successfully!")

        # Test query
        users = User.query.all()
        print(f"✅ Found {len(users)} users in database")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
```

## 5. Khởi tạo database schema

```bash
cd /path/to/your/project
source .venv/Scripts/activate
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Railway database initialized!')"
```

## 6. Production considerations

### Security:

- Railway database có SSL by default
- Connection được encrypt
- Database có firewall protection

### Performance:

- Railway cung cấp SSD storage
- Auto-scaling capabilities
- Backup tự động

### Monitoring:

- Railway dashboard cung cấp metrics
- Query monitoring
- Resource usage tracking

## 7. Migration từ localhost

Nếu đã có data trên localhost:

```bash
# Export data từ localhost
mysqldump -u root -p flask_app > backup.sql

# Import vào Railway (cần Railway CLI)
railway login
railway connect mysql
# Paste vào MySQL console
```

## 8. Environment variables cho team

Chia sẻ Railway credentials với team:

```env
# .env.railway
DATABASE_URL=mysql://root:password@host:port/railway
DB_HOST=containers-us-west-xxx.railway.app
DB_PORT=7xxx
DB_NAME=railway
DB_USER=root
DB_PASSWORD=railway_password
```

## 9. Troubleshooting

### Connection timeout:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True
}
```

### SSL issues:

```python
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl_disabled=false'
```

## 10. Free tier limitations

Railway free tier:

- $5 credit per month
- Enough cho development/testing
- Auto-sleep sau inactivity
- Upgrade nếu cần production usage
