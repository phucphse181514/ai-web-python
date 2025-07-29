# Cách tạo HTTPS tunnel cho localhost

## Option 1: Sử dụng ngrok (Miễn phí)

1. Download ngrok: https://ngrok.com/download
2. Chạy: `ngrok http 5000`
3. Sẽ được URL như: `https://abc123.ngrok.io`
4. Cập nhật .env:
   PAYOS_RETURN_URL=https://abc123.ngrok.io/payment/return
   PAYOS_CANCEL_URL=https://abc123.ngrok.io/payment/cancel

## Option 2: Sử dụng localtunnel (Miễn phí)

1. Install: `npm install -g localtunnel`
2. Chạy: `lt --port 5000`
3. Sẽ được URL như: `https://abc123.loca.lt`

## Option 3: CloudFlare Tunnel (Miễn phí)

1. Download cloudflared
2. Chạy: `cloudflared tunnel --url localhost:5000`
3. Sẽ được URL HTTPS

## Test PayOS với HTTPS

- Cập nhật PAYOS_RETURN_URL và PAYOS_CANCEL_URL trong .env
- Restart Flask app
- Test lại thanh toán
