#!/usr/bin/env python3
"""
Test script để verify cấu hình PayOS với URL hosted
"""

import os
import sys
import requests
import hashlib
import hmac
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_payos_config():
    """Test PayOS configuration với URL hosted"""
    
    print("=== PayOS Configuration Test ===")
    
    # Get config
    client_id = os.getenv('PAYOS_CLIENT_ID')
    api_key = os.getenv('PAYOS_API_KEY')
    checksum_key = os.getenv('PAYOS_CHECKSUM_KEY')
    return_url = os.getenv('PAYOS_RETURN_URL')
    cancel_url = os.getenv('PAYOS_CANCEL_URL')
    
    print(f"Client ID: {'✓' if client_id else '✗'}")
    print(f"API Key: {'✓' if api_key else '✗'}")
    print(f"Checksum Key: {'✓' if checksum_key else '✗'}")
    print(f"Return URL: {return_url}")
    print(f"Cancel URL: {cancel_url}")
    
    if not all([client_id, api_key, checksum_key, return_url, cancel_url]):
        print("❌ Missing configuration!")
        return False
    
    # Verify URLs are hosted (not localhost)
    if 'localhost' in return_url or 'localhost' in cancel_url:
        print("⚠️  Warning: URLs still pointing to localhost!")
        print("   Update .env with hosted URLs for production")
    
    # Test create payment request
    try:
        print("\n=== Testing Payment Request Creation ===")
        
        order_code = int(time.time())
        amount = 50000
        description = "MyApp Desktop"
        
        # Create signature
        signature_data = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
        signature = hmac.new(
            checksum_key.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        print(f"Order Code: {order_code}")
        print(f"Amount: {amount:,} VND")
        print(f"Description: {description}")
        print(f"Signature Data: {signature_data}")
        print(f"Signature: {signature}")
        
        # Payment request data
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
            "signature": signature
        }
        
        # Headers
        headers = {
            'x-client-id': client_id,
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        print(f"\nMaking request to PayOS API...")
        print(f"URL: https://api-merchant.payos.vn/v2/payment-requests")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(payment_data, indent=2)}")
        
        # Make request
        response = requests.post(
            'https://api-merchant.payos.vn/v2/payment-requests',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == '00':
                checkout_url = result.get('data', {}).get('checkoutUrl')
                if checkout_url:
                    print(f"✅ Payment request created successfully!")
                    print(f"📄 Checkout URL: {checkout_url}")
                    print(f"🔄 Return URL: {return_url}")
                    print(f"❌ Cancel URL: {cancel_url}")
                    return True
                else:
                    print(f"❌ No checkout URL in response")
                    return False
            else:
                print(f"❌ PayOS API error: {result.get('desc', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

def test_webhook_urls():
    """Test webhook URLs accessibility"""
    
    print("\n=== Testing Webhook URLs ===")
    
    return_url = os.getenv('PAYOS_RETURN_URL')
    cancel_url = os.getenv('PAYOS_CANCEL_URL')
    
    # Extract base URL for webhook
    if return_url:
        base_url = return_url.replace('/payment/return', '')
        webhook_url = f"{base_url}/payment/webhook"
        
        print(f"Testing webhook URL: {webhook_url}")
        
        try:
            # Test if webhook endpoint is accessible
            response = requests.get(webhook_url, timeout=10)
            if response.status_code == 405:  # Method Not Allowed is expected for GET on POST endpoint
                print(f"✅ Webhook endpoint accessible (returns 405 for GET as expected)")
            elif response.status_code == 200:
                print(f"✅ Webhook endpoint accessible")
            else:
                print(f"⚠️  Webhook endpoint returns {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Webhook endpoint not accessible: {str(e)}")
    
    # Test return URL
    if return_url:
        print(f"Testing return URL: {return_url}")
        try:
            response = requests.get(return_url, timeout=10, allow_redirects=False)
            if response.status_code in [200, 302, 401, 403]:  # Acceptable responses
                print(f"✅ Return URL accessible")
            else:
                print(f"⚠️  Return URL returns {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Return URL not accessible: {str(e)}")
    
    # Test cancel URL (dashboard)
    if cancel_url:
        print(f"Testing cancel URL: {cancel_url}")
        try:
            response = requests.get(cancel_url, timeout=10, allow_redirects=False)
            if response.status_code in [200, 302, 401, 403]:  # Acceptable responses
                print(f"✅ Cancel URL accessible")
            else:
                print(f"⚠️  Cancel URL returns {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cancel URL not accessible: {str(e)}")

def main():
    """Main test function"""
    
    print("PayOS Configuration & URL Test")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_payos_config()
    
    # Test webhook URLs if hosted
    return_url = os.getenv('PAYOS_RETURN_URL', '')
    if not 'localhost' in return_url and return_url.startswith('http'):
        test_webhook_urls()
    else:
        print("\n=== Skipping URL tests (localhost or no URL) ===")
        print("Deploy to hosted environment to test URLs")
    
    # Summary
    print("\n" + "=" * 50)
    if config_ok:
        print("✅ PayOS configuration test completed successfully!")
        print("🚀 Ready for production deployment")
    else:
        print("❌ PayOS configuration test failed!")
        print("🔧 Check your .env file and PayOS credentials")
    
    print("\nNext steps:")
    print("1. Deploy to PythonAnywhere (see DEPLOYMENT_GUIDE.md)")
    print("2. Update PayOS webhook URLs in merchant dashboard")
    print("3. Test full payment flow on production")

if __name__ == "__main__":
    main()
