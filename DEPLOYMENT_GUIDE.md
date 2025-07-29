# Hướng dẫn Deploy Flask App lên PythonAnywhere

## 1. Chuẩn bị tài khoản PythonAnywhere

1. Đăng ký tài khoản miễn phí tại [PythonAnywhere](https://www.pythonanywhere.com/)
2. Chọn username (ví dụ: `phucphuong`)
3. URL app của bạn sẽ là: `https://phucphuong.pythonanywhere.com`

## 2. Upload code lên PythonAnywhere

### Cách 1: Sử dụng Git (Khuyến nghị)

```bash
# Trong Bash console của PythonAnywhere
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### Cách 2: Upload trực tiếp

- Sử dụng Files tab trong PythonAnywhere dashboard
- Upload từng file hoặc zip file

## 3. Cấu hình Virtual Environment

```bash
# Tạo virtual environment
mkvirtualenv --python=/usr/bin/python3.10 mysite-virtualenv

# Activate virtual environment
workon mysite-virtualenv

# Install requirements
pip install -r requirements.txt
```

## 4. Cấu hình Database MySQL

### Tạo database:

1. Vào tab **Databases** trong dashboard
2. Tạo database mới (ví dụ: `phucphuong$flask_app`)
3. Tạo user và password

### Cập nhật .env:

```env
DB_HOST=phucphuong.mysql.pythonanywhere-services.com
DB_PORT=3306
DB_NAME=phucphuong$flask_app
DB_USER=phucphuong
DB_PASSWORD=your_mysql_password
```

## 5. Cấu hình Web App

### Tạo Web App:

1. Vào tab **Web** trong dashboard
2. Chọn **Add a new web app**
3. Chọn **Manual configuration**
4. Chọn **Python 3.10**

### Cấu hình WSGI file:

Chỉnh sửa file `/var/www/phucphuong_pythonanywhere_com_wsgi.py`:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/phucphuong/web'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import create_app
application = create_app()
```

### Cấu hình Virtual Environment:

- Trong tab **Web**, section **Virtualenv**
- Đường dẫn: `/home/phucphuong/.virtualenvs/mysite-virtualenv`

### Cấu hình Static Files:

- URL: `/static/`
- Directory: `/home/phucphuong/web/app/static/`

## 6. Cấu hình Environment Variables

Tạo file `.env` trong thư mục project:

```env
# Database
DB_HOST=phucphuong.mysql.pythonanywhere-services.com
DB_PORT=3306
DB_NAME=phucphuong$flask_app
DB_USER=phucphuong
DB_PASSWORD=your_mysql_password

# Flask
SECRET_KEY=your_secret_key_here
FLASK_ENV=production

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# PayOS Configuration
PAYOS_CLIENT_ID=your_payos_client_id
PAYOS_API_KEY=your_payos_api_key
PAYOS_CHECKSUM_KEY=your_payos_checksum_key
PAYOS_RETURN_URL=https://phucphuong.pythonanywhere.com/payment/return
PAYOS_CANCEL_URL=https://phucphuong.pythonanywhere.com/main/dashboard

# Payment
PAYMENT_AMOUNT=50000

# File Download
DOWNLOAD_FILE_PATH=/home/phucphuong/web/downloads/Mahika.exe
DOWNLOAD_FILE_NAME=Mahika.exe
```

## 7. Khởi tạo Database

```bash
# Trong Bash console
cd /home/phucphuong/web
workon mysite-virtualenv
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

## 8. Upload File Download

1. Tạo thư mục `downloads` trong project
2. Upload file `Mahika.exe` vào thư mục này
3. Đảm bảo đường dẫn trong `.env` đúng

## 9. Reload Web App

1. Vào tab **Web** trong dashboard
2. Click nút **Reload** màu xanh
3. Truy cập `https://phucphuong.pythonanywhere.com`

## 10. Cấu hình PayOS cho Production

### Cập nhật PayOS Merchant Dashboard:

1. Đăng nhập vào [PayOS Merchant](https://merchant.payos.vn/)
2. Vào **Cài đặt** > **Webhook**
3. Cập nhật URL:
   - **Return URL**: `https://phucphuong.pythonanywhere.com/payment/return`
   - **Cancel URL**: `https://phucphuong.pythonanywhere.com/main/dashboard`
   - **Webhook URL**: `https://phucphuong.pythonanywhere.com/payment/webhook`

## 11. Test chức năng

1. **Đăng ký tài khoản**: Test email verification
2. **Đăng nhập**: Kiểm tra authentication
3. **Thanh toán**: Test PayOS integration
4. **Download**: Kiểm tra file download sau thanh toán

## 12. Troubleshooting

### Lỗi thường gặp:

1. **500 Internal Server Error**:

   - Kiểm tra Error log trong tab **Web**
   - Kiểm tra file `.env` có đúng không
   - Kiểm tra database connection

2. **Static files không load**:

   - Kiểm tra cấu hình Static Files
   - Đảm bảo thư mục `/static/` tồn tại

3. **Database connection error**:

   - Kiểm tra thông tin database
   - Đảm bảo user có quyền truy cập database

4. **Email không gửi được**:
   - Kiểm tra App Password Gmail
   - Kiểm tra cấu hình SMTP

### Debug logs:

```bash
# Xem logs
tail -f /var/log/phucphuong.pythonanywhere.com.error.log
tail -f /var/log/phucphuong.pythonanywhere.com.server.log
```

## 13. Bảo mật Production

1. **Thay đổi SECRET_KEY**: Tạo key mới cho production
2. **Đặt FLASK_ENV=production**
3. **Sử dụng HTTPS**: PythonAnywhere tự động có SSL
4. **Bảo vệ sensitive files**: Đảm bảo `.env` không public

## 14. Monitoring và Maintenance

1. **Regular backups**: Backup database định kỳ
2. **Monitor logs**: Kiểm tra error logs thường xuyên
3. **Update dependencies**: Cập nhật packages khi cần
4. **PayOS webhook**: Monitor webhook calls trong PayOS dashboard

## Lưu ý quan trọng:

- PythonAnywhere miễn phí có giới hạn CPU và bandwidth
- File upload size có giới hạn
- Cần upgrade để có custom domain
- Webhook PayOS cần HTTPS (PythonAnywhere tự động hỗ trợ)
