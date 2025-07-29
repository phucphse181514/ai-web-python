# MyApp - Flask Web Application với Tích hợp MoMo

Ứng dụng web Flask với xác thực người dùng, xác minh email, tích hợp thanh toán MoMo và tải xuống file.

## Tính năng

- ✅ **Đăng ký/Đăng nhập người dùng** với xác thực email
- ✅ **Xác minh email** tự động gửi link xác thực
- ✅ **Quên mật khẩu** với email reset
- ✅ **Tích hợp thanh toán MoMo** cho thị trường Việt Nam
- ✅ **Tải xuống file bảo mật** chỉ cho người dùng đã thanh toán
- ✅ **Giao diện Bootstrap** responsive và đẹp mắt
- ✅ **Dashboard quản lý** trạng thái người dùng
- ✅ **Lịch sử thanh toán** chi tiết

## Cấu trúc dự án

```
web/
├── app/
│   ├── __init__.py              # Factory app
│   ├── models.py                # User & Payment models
│   ├── routes/
│   │   ├── auth.py             # Authentication routes
│   │   ├── main.py             # Main routes
│   │   └── payment.py          # MoMo payment routes
│   ├── templates/
│   │   ├── base.html           # Base template
│   │   ├── index.html          # Homepage
│   │   ├── dashboard.html      # User dashboard
│   │   ├── auth/               # Auth templates
│   │   ├── payment/            # Payment templates
│   │   └── emails/             # Email templates
│   └── static/
│       └── css/
│           └── style.css       # Custom CSS
├── downloads/                   # App files to download
├── config.py                   # Configuration
├── app.py                     # Main application file
├── requirements.txt           # Dependencies
├── .env.example              # Environment variables example
└── README.md                 # This file
```

## Cài đặt và Chạy

### 1. Clone và Setup

```bash
# Clone repository
git clone <your-repo-url>
cd web

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình Database MySQL

Tạo database MySQL:

```sql
CREATE DATABASE flask_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'flask_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON flask_app.* TO 'flask_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Cấu hình Environment Variables

Copy `.env.example` thành `.env` và cập nhật:

```bash
cp .env.example .env
```

Chỉnh sửa file `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=flask_app
DB_USER=flask_user
DB_PASSWORD=your_mysql_password

# Flask
SECRET_KEY=your-very-secret-key-here
FLASK_ENV=development

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# MoMo Configuration
MOMO_PARTNER_CODE=your_momo_partner_code
MOMO_ACCESS_KEY=your_momo_access_key
MOMO_SECRET_KEY=your_momo_secret_key
MOMO_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api/create

# Payment
PAYMENT_AMOUNT=50000

# File Download
DOWNLOAD_FILE_PATH=downloads/your-app.exe
DOWNLOAD_FILE_NAME=YourApp.exe
```

### 4. Cấu hình Email (Gmail)

1. Bật 2-Factor Authentication cho Gmail
2. Tạo App Password: Google Account → Security → 2-Step Verification → App passwords
3. Sử dụng App Password này trong `MAIL_PASSWORD`

### 5. Cấu hình MoMo

1. Đăng ký tài khoản MoMo Developer: https://developers.momo.vn/
2. Tạo ứng dụng test và lấy thông tin:
   - Partner Code
   - Access Key
   - Secret Key
3. Cập nhật vào file `.env`

### 6. Chạy ứng dụng

```bash
python app.py
```

Truy cập: http://localhost:5000

## API Endpoints

### Authentication

- `GET/POST /auth/register` - Đăng ký
- `GET/POST /auth/login` - Đăng nhập
- `GET /auth/logout` - Đăng xuất
- `GET /auth/verify-email/<token>` - Xác thực email
- `GET/POST /auth/forgot-password` - Quên mật khẩu
- `GET/POST /auth/reset-password/<token>` - Reset mật khẩu
- `GET /auth/resend-verification` - Gửi lại email xác thực

### Main

- `GET /` - Trang chủ
- `GET /dashboard` - Dashboard người dùng
- `GET /download` - Tải file ứng dụng

### Payment (MoMo)

- `GET /payment/checkout` - Trang thanh toán
- `POST /payment/create-payment` - Tạo thanh toán MoMo
- `GET /payment/return` - Xử lý kết quả thanh toán
- `POST /payment/notify` - Webhook IPN từ MoMo
- `GET /payment/history` - Lịch sử thanh toán

## Deploy lên PythonAnywhere

### 1. Upload code

```bash
# Trên PythonAnywhere console
git clone <your-repo-url>
cd web
pip3.10 install --user -r requirements.txt
```

### 2. Cấu hình Database

Tạo MySQL database trong PythonAnywhere dashboard và cập nhật `.env`.

### 3. Cấu hình Web App

1. Tạo Web App mới (Python 3.10)
2. Cập nhật WSGI file:

```python
import sys
import os

# Add your project directory to sys.path
path = '/home/yourusername/web'
if path not in sys.path:
    sys.path.append(path)

from app import create_app
application = create_app()
```

3. Cấu hình Static Files:
   - URL: `/static/`
   - Directory: `/home/yourusername/web/app/static/`

### 4. Environment Variables

Thêm vào `.env` trên server hoặc cấu hình trong code.

### 5. MoMo Webhook URL

Cập nhật webhook URL trong MoMo dashboard:

```
https://yourdomain.pythonanywhere.com/payment/notify
```

## Deploy lên VPS

### 1. Cài đặt Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx mysql-server

# Tạo user và database MySQL
sudo mysql
CREATE DATABASE flask_app;
CREATE USER 'flask_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON flask_app.* TO 'flask_user'@'localhost';
```

### 2. Setup Application

```bash
# Clone và setup
git clone <repo-url>
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Setup environment
cp .env.example .env
# Chỉnh sửa .env với thông tin thực
```

### 3. Gunicorn Service

Tạo `/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=MyApp Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/web
Environment="PATH=/path/to/web/venv/bin"
ExecStart=/path/to/web/venv/bin/gunicorn --workers 3 --bind unix:myapp.sock -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Nginx Configuration

Tạo `/etc/nginx/sites-available/myapp`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/web/myapp.sock;
    }

    location /static {
        alias /path/to/web/app/static;
    }
}
```

### 5. SSL với Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 6. Start Services

```bash
sudo systemctl start myapp
sudo systemctl enable myapp
sudo systemctl restart nginx
```

## Bảo mật

- ✅ CSRF Protection với Flask-WTF
- ✅ Password hashing với Werkzeug
- ✅ Secure session management
- ✅ Email verification required
- ✅ Payment verification với MoMo signature
- ✅ File download protection
- ✅ Environment variables cho sensitive data

## Testing MoMo

Để test MoMo trong môi trường development:

1. Sử dụng test credentials từ MoMo
2. Test với số tiền nhỏ
3. Kiểm tra webhook trên ngrok nếu develop local:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 5000

# Update MOMO webhook URL to ngrok URL
```

## Troubleshooting

### Database Issues

```bash
# Reset database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.drop_all(); db.create_all()"
```

### Email Issues

- Kiểm tra Gmail App Password
- Verify SMTP settings
- Check firewall/antivirus

### MoMo Issues

- Verify signature generation
- Check webhook URL accessibility
- Validate test credentials

## Support

- Email: support@myapp.com
- Documentation: [Wiki](link-to-wiki)
- Issues: [GitHub Issues](link-to-issues)

## License

MIT License - see LICENSE file for details.
