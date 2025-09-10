#!/usr/bin/env python3
"""
Beta Approval Service for DOTM Platform
Handles email approval workflow for beta access requests
"""

import os
import uuid
import time
from typing import Dict, Any, Optional
from email_service import send_email
from oxio_service import OXIOService
import random
import string
import json
from datetime import datetime, timedelta

class BetaApprovalService:
    def __init__(self):
        self.admin_email = os.environ.get('ADMIN_EMAIL', 'admin@dotmobile.app')
        self.approval_base_url = os.environ.get('APPROVAL_BASE_URL', 'https://gorse.dotmobile.app')
        self.oxio_service = OXIOService()

    def submit_beta_request(self, user_email: str, firebase_uid: str, user_name: str = None) -> Dict[str, Any]:
        """
        Submit a beta access request and send approval email to admin
        
        Args:
            user_email: User's email address
            firebase_uid: User's Firebase UID
            user_name: User's display name (optional)
            
        Returns:
            Dictionary with request status and details
        """
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Store request in database
            from main import get_db_connection
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create beta_requests table if it doesn't exist
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS beta_requests (
                                id VARCHAR(36) PRIMARY KEY,
                                user_email VARCHAR(255) NOT NULL,
                                firebase_uid VARCHAR(128) NOT NULL,
                                user_name VARCHAR(255),
                                status VARCHAR(50) DEFAULT 'pending',
                                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                approved_at TIMESTAMP NULL,
                                approved_by VARCHAR(255) NULL,
                                phone_number VARCHAR(20) NULL,
                                oxio_user_id VARCHAR(255) NULL,
                                oxio_group_id VARCHAR(255) NULL,
                                resin_data TEXT NULL,
                                rejection_reason TEXT NULL
                            )
                        """)
                        
                        # Insert the request
                        cur.execute("""
                            INSERT INTO beta_requests 
                            (id, user_email, firebase_uid, user_name, status) 
                            VALUES (%s, %s, %s, %s, 'pending')
                        """, (request_id, user_email, firebase_uid, user_name))
                        
                        conn.commit()
            
            # Send approval email to admin
            approval_url = f"{self.approval_base_url}/api/beta-approve/{request_id}"
            reject_url = f"{self.approval_base_url}/api/beta-reject/{request_id}"
            
            subject = f"Beta Access Request - {user_email}"
            
            body = f"""
New Beta Access Request

User Details:
- Email: {user_email}
- Name: {user_name or 'Not provided'}
- Firebase UID: {firebase_uid}
- Request ID: {request_id}

Actions:
- Approve: {approval_url}
- Reject: {reject_url}

This request requires manual approval before the user can access beta features.
"""
            
            html_body = f"""
<html>
<body>
    <h2>New Beta Access Request</h2>
    
    <h3>User Details:</h3>
    <ul>
        <li><strong>Email:</strong> {user_email}</li>
        <li><strong>Name:</strong> {user_name or 'Not provided'}</li>
        <li><strong>Firebase UID:</strong> {firebase_uid}</li>
        <li><strong>Request ID:</strong> {request_id}</li>
    </ul>
    
    <h3>Actions:</h3>
    <p>
        <a href="{approval_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            ✅ APPROVE
        </a>
        &nbsp;&nbsp;&nbsp;
        <a href="{reject_url}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            ❌ REJECT
        </a>
    </p>
    
    <p><em>This request requires manual approval before the user can access beta features.</em></p>
</body>
</html>
"""
            
            # Send email to admin
            email_sent = send_email(self.admin_email, subject, body, html_body)
            
            return {
                'success': True,
                'request_id': request_id,
                'message': 'Beta request submitted successfully',
                'email_sent': email_sent
            }
            
        except Exception as e:
            print(f"Error submitting beta request: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to submit beta request'
            }

    def approve_beta_request(self, request_id: str, approved_by: str = 'admin') -> Dict[str, Any]:
        """
        Approve a beta request and trigger OXIO activation
        
        Args:
            request_id: The beta request ID
            approved_by: Email of the person approving
            
        Returns:
            Dictionary with approval status and activation details
        """
        try:
            from main import get_db_connection
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get request details
                        cur.execute("""
                            SELECT user_email, firebase_uid, user_name, status 
                            FROM beta_requests 
                            WHERE id = %s
                        """, (request_id,))
                        
                        request_data = cur.fetchone()
                        if not request_data:
                            return {
                                'success': False,
                                'error': 'Request not found',
                                'message': 'Beta request not found'
                            }
                        
                        user_email, firebase_uid, user_name, status = request_data
                        
                        if status != 'pending':
                            return {
                                'success': False,
                                'error': 'Request already processed',
                                'message': f'Request status is: {status}'
                            }
                        
                        # Generate random phone number for North America
                        phone_number = self._generate_random_phone_number()
                        
                        # Create OXIO user and GroupID
                        oxio_result = self._create_oxio_user_and_group(
                            user_email, 
                            user_name, 
                            firebase_uid
                        )
                        
                        if not oxio_result['success']:
                            return {
                                'success': False,
                                'error': 'OXIO activation failed',
                                'message': oxio_result.get('message', 'Failed to create OXIO user')
                            }
                        
                        # Update request as approved
                        cur.execute("""
                            UPDATE beta_requests 
                            SET status = 'approved', 
                                approved_at = CURRENT_TIMESTAMP,
                                approved_by = %s,
                                phone_number = %s,
                                oxio_user_id = %s,
                                oxio_group_id = %s,
                                resin_data = %s
                            WHERE id = %s
                        """, (
                            approved_by, 
                            phone_number,
                            oxio_result.get('oxio_user_id'),
                            oxio_result.get('group_id'),
                            json.dumps(oxio_result.get('resin_data', {})),
                            request_id
                        ))
                        
                        conn.commit()
                        
                        # Send confirmation email to user
                        self._send_approval_confirmation_email(
                            user_email, 
                            user_name, 
                            phone_number,
                            oxio_result
                        )
                        
                        return {
                            'success': True,
                            'message': 'Beta request approved successfully',
                            'phone_number': phone_number,
                            'oxio_user_id': oxio_result.get('oxio_user_id'),
                            'group_id': oxio_result.get('group_id')
                        }
                        
        except Exception as e:
            print(f"Error approving beta request: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to approve beta request'
            }

    def reject_beta_request(self, request_id: str, reason: str = None, rejected_by: str = 'admin') -> Dict[str, Any]:
        """
        Reject a beta request
        
        Args:
            request_id: The beta request ID
            reason: Reason for rejection (optional)
            rejected_by: Email of the person rejecting
            
        Returns:
            Dictionary with rejection status
        """
        try:
            from main import get_db_connection
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get request details
                        cur.execute("""
                            SELECT user_email, user_name, status 
                            FROM beta_requests 
                            WHERE id = %s
                        """, (request_id,))
                        
                        request_data = cur.fetchone()
                        if not request_data:
                            return {
                                'success': False,
                                'error': 'Request not found'
                            }
                        
                        user_email, user_name, status = request_data
                        
                        if status != 'pending':
                            return {
                                'success': False,
                                'error': 'Request already processed',
                                'message': f'Request status is: {status}'
                            }
                        
                        # Update request as rejected
                        cur.execute("""
                            UPDATE beta_requests 
                            SET status = 'rejected',
                                approved_at = CURRENT_TIMESTAMP,
                                approved_by = %s,
                                rejection_reason = %s
                            WHERE id = %s
                        """, (rejected_by, reason, request_id))
                        
                        conn.commit()
                        
                        # Send rejection email to user
                        self._send_rejection_email(user_email, user_name, reason)
                        
                        return {
                            'success': True,
                            'message': 'Beta request rejected'
                        }
                        
        except Exception as e:
            print(f"Error rejecting beta request: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_random_phone_number(self) -> str:
        """Generate a random North American phone number"""
        # Area codes for major North American cities
        area_codes = ['212', '213', '312', '415', '617', '647', '514', '604']
        area_code = random.choice(area_codes)
        
        # Generate 7-digit number (XXX-XXXX format)
        exchange = str(random.randint(200, 999))  # First 3 digits (avoid 0xx, 1xx)
        number = str(random.randint(1000, 9999))  # Last 4 digits
        
        return f"+1{area_code}{exchange}{number}"

    def _create_oxio_user_and_group(self, email: str, name: str, firebase_uid: str) -> Dict[str, Any]:
        """Create OXIO user and generate GroupID"""
        try:
            # Generate unique GroupID
            group_id = f"DOTM-{int(time.time())}-{random.randint(1000, 9999)}"
            
            # Create OXIO user
            oxio_result = self.oxio_service.create_oxio_user(
                first_name=name.split(' ')[0] if name else 'Beta',
                last_name=name.split(' ')[-1] if name and ' ' in name else 'User',
                email=email,
                firebase_uid=firebase_uid,
                oxio_group_id=group_id
            )
            
            if oxio_result.get('success'):
                return {
                    'success': True,
                    'oxio_user_id': oxio_result.get('user_id'),
                    'group_id': group_id,
                    'resin_data': {
                        'group_id': group_id,
                        'created_at': datetime.now().isoformat(),
                        'firebase_uid': firebase_uid,
                        'email': email
                    }
                }
            else:
                return {
                    'success': False,
                    'message': oxio_result.get('message', 'Failed to create OXIO user')
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def _send_approval_confirmation_email(self, user_email: str, user_name: str, phone_number: str, oxio_result: Dict):
        """Send confirmation email to approved user"""
        subject = "🎉 Your Beta Access Request Has Been Approved!"
        
        body = f"""
Congratulations {user_name or 'Beta User'}!

Your beta access request has been approved. Here are your details:

📱 Phone Number: {phone_number}
🆔 Group ID: {oxio_result.get('group_id')}
👤 OXIO User ID: {oxio_result.get('oxio_user_id')}

You can now access beta features in your profile. Visit your profile page to see your phone numbers and QR codes.

Welcome to the DOTM beta program!

Best regards,
DOTM Team
"""
        
        html_body = f"""
<html>
<body>
    <h2>🎉 Beta Access Approved!</h2>
    
    <p>Congratulations <strong>{user_name or 'Beta User'}</strong>!</p>
    
    <p>Your beta access request has been approved. Here are your details:</p>
    
    <ul>
        <li><strong>📱 Phone Number:</strong> {phone_number}</li>
        <li><strong>🆔 Group ID:</strong> {oxio_result.get('group_id')}</li>
        <li><strong>👤 OXIO User ID:</strong> {oxio_result.get('oxio_user_id')}</li>
    </ul>
    
    <p>You can now access beta features in your profile. Visit your profile page to see your phone numbers and QR codes.</p>
    
    <p><strong>Welcome to the DOTM beta program!</strong></p>
    
    <p>Best regards,<br><strong>DOTM Team</strong></p>
</body>
</html>
"""
        
        send_email(user_email, subject, body, html_body)

    def _send_rejection_email(self, user_email: str, user_name: str, reason: str = None):
        """Send rejection email to user"""
        subject = "Beta Access Request Update"
        
        body = f"""
Hello {user_name or 'User'},

Thank you for your interest in the DOTM beta program. After review, we are unable to approve your beta access request at this time.

{f'Reason: {reason}' if reason else ''}

You can apply again in the future as we continue to expand our beta program.

Best regards,
DOTM Team
"""
        
        html_body = f"""
<html>
<body>
    <h2>Beta Access Request Update</h2>
    
    <p>Hello <strong>{user_name or 'User'}</strong>,</p>
    
    <p>Thank you for your interest in the DOTM beta program. After review, we are unable to approve your beta access request at this time.</p>
    
    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
    
    <p>You can apply again in the future as we continue to expand our beta program.</p>
    
    <p>Best regards,<br><strong>DOTM Team</strong></p>
</body>
</html>
"""
        
        send_email(user_email, subject, body, html_body)

    def get_user_beta_status(self, firebase_uid: str) -> Dict[str, Any]:
        """Get beta status for a user"""
        try:
            from main import get_db_connection
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT status, phone_number, oxio_user_id, oxio_group_id, 
                                   resin_data, requested_at, approved_at
                            FROM beta_requests 
                            WHERE firebase_uid = %s 
                            ORDER BY requested_at DESC 
                            LIMIT 1
                        """, (firebase_uid,))
                        
                        result = cur.fetchone()
                        if result:
                            status, phone_number, oxio_user_id, oxio_group_id, resin_data, requested_at, approved_at = result
                            return {
                                'has_request': True,
                                'status': status,
                                'phone_number': phone_number,
                                'oxio_user_id': oxio_user_id,
                                'group_id': oxio_group_id,
                                'resin_data': json.loads(resin_data) if resin_data else {},
                                'requested_at': requested_at.isoformat() if requested_at else None,
                                'approved_at': approved_at.isoformat() if approved_at else None
                            }
                        else:
                            return {
                                'has_request': False,
                                'status': 'none'
                            }
                            
        except Exception as e:
            print(f"Error getting beta status: {str(e)}")
            return {
                'has_request': False,
                'status': 'error',
                'error': str(e)
            }