# Hướng dẫn Cấu hình PayOS Integration

## 1. Đăng ký PayOS Merchant Account

1. Truy cập [PayOS Merchant Portal](https://merchant.payos.vn/)
2. Đăng ký tài khoản merchant
3. Hoàn thành xác thực KYC (Know Your Customer)
4. Chờ PayOS phê duyệt tài khoản

## 2. Lấy API Credentials

Sau khi tài khoản được phê duyệt:

1. Đăng nhập vào PayOS Merchant Portal
2. Vào **Cài đặt** > **API Keys**
3. Lấy các thông tin:
   - **Client ID**: Định danh ứng dụng
   - **API Key**: Key để xác thực API calls
   - **Checksum Key**: Key để tạo signature bảo mật

## 3. Cấu hình Webhook URLs

### Trong PayOS Merchant Portal:

1. Vào **Cài đặt** > **Webhook Configuration**
2. Cập nhật các URL:

#### Development (localhost):

```
Return URL: http://localhost:5000/payment/return
Cancel URL: http://localhost:5000/main/dashboard
Webhook URL: https://your-ngrok-url.ngrok.io/payment/webhook
```

#### Production (PythonAnywhere):

```
Return URL: https://phucphuong.pythonanywhere.com/payment/return
Cancel URL: https://phucphuong.pythonanywhere.com/main/dashboard
Webhook URL: https://phucphuong.pythonanywhere.com/payment/webhook
```

## 4. Cấu hình Environment Variables

### File .env cho Development:

```env
# PayOS Configuration
PAYOS_CLIENT_ID=your_payos_client_id_here
PAYOS_API_KEY=your_payos_api_key_here
PAYOS_CHECKSUM_KEY=your_payos_checksum_key_here
PAYOS_RETURN_URL=http://localhost:5000/payment/return
PAYOS_CANCEL_URL=http://localhost:5000/main/dashboard
```

### File .env cho Production:

```env
# PayOS Configuration
PAYOS_CLIENT_ID=your_payos_client_id_here
PAYOS_API_KEY=your_payos_api_key_here
PAYOS_CHECKSUM_KEY=your_payos_checksum_key_here
PAYOS_RETURN_URL=https://phucphuong.pythonanywhere.com/payment/return
PAYOS_CANCEL_URL=https://phucphuong.pythonanywhere.com/main/dashboard
```

## 5. PayOS API Flow

### 5.1 Tạo Payment Request

```python
def create_payment_request():
    # Tạo order code unique
    order_code = int(time.time())
    amount = 50000  # VND

    # Tạo signature
    signature_data = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
    signature = hmac.new(
        checksum_key.encode(),
        signature_data.encode(),
        hashlib.sha256
    ).hexdigest()

    # Payment data
    payment_data = {
        "orderCode": order_code,
        "amount": amount,
        "description": "MyApp Desktop",  # Max 25 ký tự
        "returnUrl": return_url,
        "cancelUrl": cancel_url,
        "signature": signature
    }

    # Call PayOS API
    response = requests.post(
        'https://api-merchant.payos.vn/v2/payment-requests',
        headers={
            'x-client-id': client_id,
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        },
        json=payment_data
    )
```

### 5.2 Xử lý Return URL

Khi user hoàn thành thanh toán, PayOS sẽ redirect về `return_url` với params:

```python
@payment_bp.route('/return')
def payment_return():
    order_code = request.args.get('orderCode')
    code = request.args.get('code')
    cancel = request.args.get('cancel')

    if code == '00':
        # Payment thành công
        update_payment_status(order_code, 'PAID')
        flash('Thanh toán thành công!', 'success')
    elif cancel == 'true':
        # Payment bị hủy
        update_payment_status(order_code, 'CANCELLED')
        flash('Thanh toán đã bị hủy', 'warning')
    else:
        # Payment thất bại
        update_payment_status(order_code, 'FAILED')
        flash('Thanh toán thất bại', 'error')

    return redirect(url_for('main.dashboard'))
```

### 5.3 Xử lý Webhook

PayOS sẽ gửi webhook notification khi payment status thay đổi:

```python
@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    data = request.get_json()
    webhook_data = data.get('data', {})

    order_code = webhook_data.get('orderCode')
    amount = webhook_data.get('amount')
    reference = webhook_data.get('reference')

    # Update payment in database
    payment = Payment.query.filter_by(payos_order_id=str(order_code)).first()
    if payment and payment.status == 'PENDING':
        payment.status = 'PAID'
        payment.payos_transaction_id = reference
        payment.completed_at = datetime.utcnow()

        # Update user payment status
        payment.user.has_paid = True
        db.session.commit()

    return jsonify({'code': '00', 'desc': 'Success'}), 200
```

## 6. Testing PayOS Integration

### 6.1 Test với localhost (Development)

1. **Cài đặt ngrok** để tạo HTTPS tunnel:

```bash
# Download ngrok từ https://ngrok.com/
ngrok http 5000
```

2. **Cập nhật webhook URL** trong PayOS dashboard với ngrok URL

3. **Test payment flow**:
   - Đăng ký user mới
   - Xác thực email
   - Thực hiện thanh toán
   - Kiểm tra webhook được gọi

### 6.2 Test với Production

1. **Deploy lên PythonAnywhere**
2. **Cập nhật webhook URLs** trong PayOS dashboard
3. **Test đầy đủ user journey**

## 7. PayOS Sandbox vs Production

### Sandbox Environment:

- Dùng để test integration
- Không có giao dịch thật
- API endpoint: `https://api-merchant-sandbox.payos.vn`

### Production Environment:

- Giao dịch thật
- Cần KYC và phê duyệt
- API endpoint: `https://api-merchant.payos.vn`

## 8. Các lỗi thường gặp

### 8.1 "Mô tả tối đa 25 kí tự"

```python
# Đảm bảo description <= 25 ký tự
description = "MyApp Desktop"  # OK - 14 ký tự
description = "Payment for MyApp Desktop Application"  # ERROR - > 25 ký tự
```

### 8.2 Signature không đúng

```python
# Thứ tự params trong signature phải đúng alphabet
signature_data = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
```

### 8.3 Webhook không nhận được

- Kiểm tra URL có HTTPS không
- Kiểm tra firewall settings
- Kiểm tra PayOS dashboard configuration

## 9. Security Best Practices

### 9.1 Bảo vệ API Keys

```python
# Không hardcode keys trong source code
# Sử dụng environment variables
PAYOS_API_KEY = os.getenv('PAYOS_API_KEY')
```

### 9.2 Validate Webhook

```python
# Verify webhook signature để đảm bảo request từ PayOS
def verify_webhook_signature(request_data, signature):
    expected_signature = hmac.new(
        checksum_key.encode(),
        request_data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

### 9.3 Handle Duplicates

```python
# Kiểm tra duplicate payments
existing_payment = Payment.query.filter_by(payos_order_id=order_code).first()
if existing_payment:
    return redirect(url_for('main.dashboard'))
```

## 10. Monitoring và Logging

### 10.1 Log PayOS API calls

```python
import logging

logger = logging.getLogger(__name__)

def call_payos_api(data):
    logger.info(f'PayOS API call: {data}')
    response = requests.post(url, json=data)
    logger.info(f'PayOS response: {response.status_code} - {response.text}')
    return response
```

### 10.2 Monitor webhook calls

```python
@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    logger.info(f'Webhook received: {request.get_json()}')
    # Process webhook
    logger.info(f'Webhook processed successfully')
```

## 11. PayOS Dashboard Features

### 11.1 Transaction Monitoring

- Xem tất cả transactions
- Filter theo status, date
- Export reports

### 11.2 Refund Management

- Tạo refund requests
- Track refund status

### 11.3 Settlement Reports

- Xem báo cáo điều tiết
- Download settlement files

## 12. Support và Documentation

- **PayOS Developer Docs**: [https://docs.payos.vn](https://docs.payos.vn)
- **Merchant Portal**: [https://merchant.payos.vn](https://merchant.payos.vn)
- **Support Email**: support@payos.vn
- **Telegram Support**: @payos_support
