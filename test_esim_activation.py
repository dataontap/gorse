
#!/usr/bin/env python3
"""
Test script for the new eSIM activation service
"""

import sys
import json
from esim_activation_service import esim_activation_service

def test_esim_activation():
    """Test the eSIM activation service with sample data"""
    
    # Test parameters
    test_firebase_uid = "test_firebase_uid_123"
    test_email = "test@example.com"
    test_name = "Test User"
    test_stripe_session = "cs_test_123456789"
    test_amount = 100  # $1.00 in cents
    
    print(f"🧪 Testing eSIM activation service")
    print(f"   Firebase UID: {test_firebase_uid}")
    print(f"   Email: {test_email}")
    print(f"   Name: {test_name}")
    print(f"   Amount: ${test_amount/100:.2f}")
    print("-" * 50)
    
    # Call the activation service
    result = esim_activation_service.activate_esim_after_payment(
        firebase_uid=test_firebase_uid,
        user_email=test_email,
        user_name=test_name,
        stripe_session_id=test_stripe_session,
        purchase_amount=test_amount
    )
    
    print("\n📊 Activation Result:")
    print(json.dumps(result, indent=2, default=str))
    
    if result.get('success'):
        print("\n✅ eSIM activation test completed successfully!")
        esim_data = result.get('esim_data', {})
        print(f"   📱 Phone: {esim_data.get('phone_number', 'N/A')}")
        print(f"   🏷️  Line ID: {esim_data.get('line_id', 'N/A')}")
        print(f"   📷 QR Code: {'Available' if esim_data.get('qr_code') else 'Not generated'}")
        print(f"   🪙 Token Reward: {result.get('token_reward', {}).get('success', False)}")
        print(f"   📧 Email Sent: {result.get('email_sent', False)}")
    else:
        print(f"\n❌ eSIM activation test failed:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Step: {result.get('step', 'Unknown step')}")
    
    return result

if __name__ == "__main__":
    test_esim_activation()
