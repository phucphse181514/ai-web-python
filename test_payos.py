#!/usr/bin/env python3
"""
Test script để kiểm tra PayOS API trực tiếp
"""

import requests
import json
import hashlib
import hmac
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_payos_api():
    """Test PayOS API với các thông tin cấu hình"""
    
    # PayOS configuration
    client_id = os.getenv('PAYOS_CLIENT_ID')
    api_key = os.getenv('PAYOS_API_KEY')
    checksum_key = os.getenv('PAYOS_CHECKSUM_KEY')
    return_url = os.getenv('PAYOS_RETURN_URL')
    cancel_url = os.getenv('PAYOS_CANCEL_URL')
    
    print("=== PayOS API Test ===")
    print(f"Client ID: {client_id}")
    print(f"API Key: {api_key[:10]}..." if api_key else "None")
    print(f"Checksum Key: {checksum_key[:10]}..." if checksum_key else "None")
    print(f"Return URL: {return_url}")
    print(f"Cancel URL: {cancel_url}")    print()
    
    if not all([client_id, api_key, checksum_key]):
        print("❌ PayOS configuration incomplete!")
        return False
    
    # Payment data - format theo PayOS documentation v2
    order_code = int(datetime.now().timestamp())  # PayOS yêu cầu unique orderCode
    amount = 50000
    
    # Cần tạo signature theo PayOS format
    signature_data = {
        "amount": amount,
        "cancelUrl": cancel_url,
        "description": "Test payment",
        "orderCode": order_code,
        "returnUrl": return_url
    }
    
    # Tạo signature
    sorted_keys = sorted(signature_data.keys())
    query_string = '&'.join([f"{key}={signature_data[key]}" for key in sorted_keys])
    signature = hmac.new(
        checksum_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    payment_data = {
        "orderCode": order_code,
        "amount": amount,
        "description": "Test payment",
        "returnUrl": return_url,
        "cancelUrl": cancel_url,
        "signature": signature
    }
    
    print("Payment Data:")
    print(json.dumps(payment_data, indent=2))
    print()
    
    # Headers
    headers = {
        'x-client-id': client_id,
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Headers:")
    print(json.dumps(headers, indent=2))    print()
    
    # Make request
    try:
        print("Making request to PayOS API...")
        response = requests.post(
            'https://api-merchant.payos.vn/v2/payment-requests',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Response:")
            print(json.dumps(result, indent=2))
            
            if result.get('code') == '00':
                checkout_url = result.get('data', {}).get('checkoutUrl')
                print(f"\n✅ Checkout URL: {checkout_url}")
                return True
            else:
                print(f"❌ PayOS Error: {result.get('desc', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print("Response body:")
            print(response.text)
            return False
            
    except requests.RequestException as e:
        print(f"❌ Request Exception: {e}")
        return False
    except Exception as e:
        print(f"❌ General Exception: {e}")
        return False

if __name__ == "__main__":
    test_payos_api()
