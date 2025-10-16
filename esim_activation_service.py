import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from oxio_service import oxio_service

class eSIMActivationService:
    def __init__(self):
        self.oxio_service = oxio_service

    def activate_esim_after_payment(self, 
                                   firebase_uid: str, 
                                   user_email: str, 
                                   user_name: str = None,
                                   stripe_session_id: str = None,
                                   purchase_amount: int = 100) -> Dict[str, Any]:
        """
        Complete eSIM activation workflow after successful Stripe payment

        Args:
            firebase_uid: User's Firebase UID
            user_email: User's email address
            user_name: User's display name (optional)
            stripe_session_id: Stripe checkout session ID
            purchase_amount: Payment amount in cents

        Returns:
            Dictionary with activation results
        """
        try:
            print(f"🎯 Starting eSIM activation workflow for Firebase UID: {firebase_uid}")

            # Step 1: Get or create user data in database
            user_data = self._get_or_create_user_data(firebase_uid, user_email, user_name)
            if not user_data:
                return {
                    'success': False,
                    'error': 'Failed to get/create user data',
                    'step': 'user_data_creation'
                }

            user_id = user_data['user_id']
            existing_oxio_user_id = user_data.get('oxio_user_id')
            existing_oxio_group_id = user_data.get('oxio_group_id')

            print(f"📊 User data: ID={user_id}, OXIO User={existing_oxio_user_id}, OXIO Group={existing_oxio_group_id}")

            # Step 2: Ensure OXIO user exists first (needed for group creation)
            oxio_user_id = self._ensure_oxio_user(
                user_id, firebase_uid, user_email, user_name, 
                existing_oxio_user_id  # Groups excluded entirely
            )
            if not oxio_user_id:
                return {
                    'success': False,
                    'error': 'Failed to create/get OXIO user',
                    'step': 'oxio_user_creation'
                }

            # Step 3: OXIO Groups disabled - continue without group ID to prevent webhook failures
            oxio_group_id = None  # Groups excluded entirely from activation flow

            # Step 4: Activate eSIM line with proper payload structure
            activation_result = self._activate_esim_line(oxio_user_id)
            if not activation_result.get('success'):
                return {
                    'success': False,
                    'error': f"eSIM activation failed: {activation_result.get('message', 'Unknown error')}",
                    'step': 'esim_activation',
                    'oxio_response': activation_result
                }

            # Step 5: Process activation data and store results
            esim_data = self._process_activation_data(activation_result)

            # Step 6: Store activation record in database
            stored_activation = self._store_activation_record(
                user_id, firebase_uid, stripe_session_id, esim_data, activation_result
            )

            # Step 7: Update Users table with eSIM details for profile display
            self._update_user_esim_details(
                firebase_uid, 
                phone_number=esim_data.get('phone_number'),
                lpa_address=esim_data.get('activation_url'),
                iccid=esim_data.get('iccid'),
                qr_code=esim_data.get('qr_code')
            )

            # Step 8: Award tokens for purchase (10.33% reward)
            token_result = self._award_purchase_tokens(user_data.get('eth_address'), purchase_amount)

            # Step 9: Send confirmation email
            email_sent = self._send_activation_email(
                user_email, user_name, esim_data, oxio_user_id
            )

            return {
                'success': True,
                'message': 'eSIM activation completed successfully',
                'esim_data': esim_data,
                'oxio_user_id': oxio_user_id,
                'oxio_group_id': oxio_group_id,
                'activation_id': stored_activation.get('activation_id'),
                'token_reward': token_result,
                'email_sent': email_sent,
                'stripe_session_id': stripe_session_id
            }

        except Exception as e:
            print(f"❌ Error in eSIM activation workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'step': 'workflow_exception'
            }

    def _get_or_create_user_data(self, firebase_uid: str, user_email: str, user_name: str = None) -> Optional[Dict[str, Any]]:
        """Get user data from database or create if missing"""
        try:
            from main import get_db_connection, get_user_by_firebase_uid

            # Try to get existing user
            user_data = get_user_by_firebase_uid(firebase_uid)
            if user_data:
                return {
                    'user_id': user_data.get('id'),
                    'email': user_data.get('email'),
                    'oxio_user_id': user_data.get('oxio_user_id'),
                    'eth_address': user_data.get('eth_address'),
                    'oxio_group_id': user_data.get('oxio_group_id')
                }

            # Create new user if not found
            print(f"🆕 Creating new user for Firebase UID: {firebase_uid}")
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create Sepolia test wallet
                        from web3 import Web3
                        web3 = Web3()
                        test_account = web3.eth.account.create()

                        cur.execute("""
                            INSERT INTO users 
                            (email, firebase_uid, display_name, eth_address) 
                            VALUES (%s, %s, %s, %s) 
                            RETURNING id
                        """, (user_email, firebase_uid, user_name, test_account.address))

                        user_id = cur.fetchone()[0]
                        conn.commit()

                        print(f"✅ Created new user: {user_id} with wallet: {test_account.address}")

                        return {
                            'user_id': user_id,
                            'email': user_email,
                            'oxio_user_id': None,
                            'eth_address': test_account.address,
                            'oxio_group_id': None
                        }

            return None

        except Exception as e:
            print(f"❌ Error getting/creating user data: {str(e)}")
            return None

    def _ensure_oxio_group(self, user_id: int, firebase_uid: str, existing_group_id: str = None, oxio_user_id: str = None) -> Optional[str]:
        """DISABLED: OXIO group creation removed to prevent Stripe webhook failures"""
        # OXIO groups are disabled entirely from the eSIM activation flow
        # Groups caused webhook failures and are not required for eSIM activation
        # The system works perfectly with just OXIO users (endUserId) for line activation
        print(f"⚠️ OXIO groups disabled - continuing without group (webhook stability)")
        return None

    def _ensure_oxio_user(self, user_id: int, firebase_uid: str, user_email: str, 
                               user_name: str = None, existing_user_id: str = None) -> Optional[str]:
        """Ensure OXIO user exists"""
        try:
            if existing_user_id:
                print(f"✅ Using existing OXIO user: {existing_user_id}")
                return existing_user_id

            # Try to find existing user by email first
            print(f"🔍 Searching for existing OXIO user by email: {user_email}")
            existing_user_result = self.oxio_service.find_user_by_email(user_email)

            if existing_user_result.get('success'):
                oxio_user_id = existing_user_result.get('oxio_user_id')
                print(f"✅ Found existing OXIO user: {oxio_user_id}")

                # Update user record with found OXIO user ID
                self._update_user_oxio_data(firebase_uid, oxio_user_id=oxio_user_id)

                return oxio_user_id

            # Create new OXIO user
            name_parts = (user_name or "Anonymous User").split(' ', 1)
            first_name = name_parts[0] if name_parts else "Anonymous"
            last_name = name_parts[1] if len(name_parts) > 1 else "User"

            print(f"🆕 Creating new OXIO user: {first_name} {last_name}")
            user_result = self.oxio_service.create_oxio_user(
                first_name=first_name,
                last_name=last_name,
                email=user_email,
                firebase_uid=firebase_uid
                # oxio_group_id removed - groups excluded from activation flow
            )

            if user_result.get('success'):
                oxio_user_id = user_result.get('oxio_user_id')
                print(f"✅ Created OXIO user: {oxio_user_id}")

                # Update user record with new OXIO user ID
                self._update_user_oxio_data(firebase_uid, oxio_user_id=oxio_user_id)

                return oxio_user_id
            else:
                print(f"❌ Failed to create OXIO user: {user_result.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"❌ Error ensuring OXIO user: {str(e)}")
            return None

    def _activate_esim_line(self, oxio_user_id: str) -> Dict[str, Any]:
        """Activate eSIM line using the corrected payload structure"""
        try:
            # Create the exact payload structure from the curl command
            activation_payload = {
                "lineType": "LINE_TYPE_MOBILITY",
                "countryCode": "US",
                "sim": {
                    "simType": "EMBEDDED"
                },
                "phoneNumberRequirements": {
                    "preferredAreaCode": "212"
                },
                "endUserId": oxio_user_id,
                "activateOnAttach": False
            }

            print(f"🚀 Activating eSIM line for OXIO user: {oxio_user_id}")
            print(f"📝 Payload structure: {json.dumps(activation_payload, indent=2)}")

            # Call OXIO activation service
            result = self.oxio_service.activate_line(activation_payload)

            if result.get('success'):
                print(f"✅ eSIM line activation successful")
                return result
            else:
                print(f"❌ eSIM line activation failed: {result.get('message', 'Unknown error')}")
                return result

        except Exception as e:
            print(f"❌ Error activating eSIM line: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Exception during eSIM activation'
            }

    def _process_activation_data(self, activation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and extract eSIM activation data"""
        try:
            activation_data = activation_result.get('data', {})

            # Extract phone number from phoneNumbers array
            phone_numbers = activation_data.get('phoneNumbers', [])
            phone_number = phone_numbers[0].get('phoneNumber') if phone_numbers and len(phone_numbers) > 0 else None

            # Extract SIM details
            sim_data = activation_data.get('sim', {})
            
            esim_data = {
                'phone_number': phone_number,
                'line_id': activation_data.get('lineId'),
                'iccid': activation_data.get('iccid') or sim_data.get('iccid'),
                'activation_status': 'activated',
                'activation_date': datetime.now().isoformat(),
                'qr_code': self._generate_esim_qr_code(activation_data),
                'activation_url': sim_data.get('activationUrl'),
                'activation_code': sim_data.get('activationCode')
            }

            print(f"📱 Processed eSIM data: Phone={esim_data['phone_number']}, Line={esim_data['line_id']}, ICCID={esim_data['iccid']}")

            return esim_data

        except Exception as e:
            print(f"❌ Error processing activation data: {str(e)}")
            return {}

    def _generate_esim_qr_code(self, activation_data: Dict[str, Any]) -> Optional[str]:
        """Generate QR code for eSIM activation"""
        try:
            import qrcode
            import base64
            from io import BytesIO

            # Use activation URL if available, otherwise create LPA format
            qr_data = activation_data.get('activationUrl')
            if not qr_data:
                iccid = activation_data.get('iccid') or activation_data.get('sim', {}).get('iccid')
                if iccid:
                    qr_data = f"LPA:1$consumer.e-sim.global${iccid}$"
                else:
                    return None

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            print(f"✅ Generated eSIM QR code successfully")
            return qr_base64

        except Exception as e:
            print(f"❌ Error generating QR code: {str(e)}")
            return None

    def _store_activation_record(self, user_id: int, firebase_uid: str, stripe_session_id: str,
                                esim_data: Dict[str, Any], activation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Store activation record in database"""
        try:
            from main import get_db_connection

            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Ensure oxio_activations table exists with all required columns
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS oxio_activations (
                                id SERIAL PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                firebase_uid VARCHAR(128),
                                purchase_id VARCHAR(200),
                                product_id VARCHAR(100),
                                iccid VARCHAR(50),
                                line_id VARCHAR(100),
                                phone_number VARCHAR(20),
                                activation_status VARCHAR(50),
                                plan_id VARCHAR(100),
                                group_id VARCHAR(100),
                                esim_qr_code TEXT,
                                activation_url VARCHAR(500),
                                activation_code VARCHAR(200),
                                oxio_response TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)

                        # Insert activation record
                        cur.execute("""
                            INSERT INTO oxio_activations 
                            (user_id, firebase_uid, purchase_id, product_id, iccid, 
                             line_id, phone_number, activation_status, esim_qr_code,
                             activation_url, activation_code, oxio_response)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            user_id, firebase_uid, stripe_session_id, 'esim_beta',
                            esim_data.get('iccid'), esim_data.get('line_id'),
                            esim_data.get('phone_number'), esim_data.get('activation_status'),
                            esim_data.get('qr_code'), esim_data.get('activation_url'),
                            esim_data.get('activation_code'), json.dumps(activation_result)
                        ))

                        activation_id = cur.fetchone()[0]
                        conn.commit()

                        print(f"💾 Stored activation record: {activation_id}")

                        return {'activation_id': activation_id, 'success': True}

            return {'success': False, 'error': 'No database connection'}

        except Exception as e:
            print(f"❌ Error storing activation record: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _update_user_oxio_data(self, firebase_uid: str, oxio_user_id: str = None, oxio_group_id: str = None):
        """Update user record with OXIO data"""
        try:
            from main import get_db_connection

            if not oxio_user_id and not oxio_group_id:
                return

            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        if oxio_user_id and oxio_group_id:
                            cur.execute("""
                                UPDATE users SET oxio_user_id = %s, oxio_group_id = %s 
                                WHERE firebase_uid = %s
                            """, (oxio_user_id, oxio_group_id, firebase_uid))
                        elif oxio_user_id:
                            cur.execute("""
                                UPDATE users SET oxio_user_id = %s 
                                WHERE firebase_uid = %s
                            """, (oxio_user_id, firebase_uid))
                        elif oxio_group_id:
                            cur.execute("""
                                UPDATE users SET oxio_group_id = %s 
                                WHERE firebase_uid = %s
                            """, (oxio_group_id, firebase_uid))

                        conn.commit()
                        print(f"✅ Updated user OXIO data for {firebase_uid}")

        except Exception as e:
            print(f"❌ Error updating user OXIO data: {str(e)}")

    def _update_user_esim_details(self, firebase_uid: str, phone_number: str = None, 
                                   lpa_address: str = None, iccid: str = None, qr_code: str = None):
        """Update user record with eSIM details for profile display"""
        try:
            from main import get_db_connection

            if not any([phone_number, lpa_address, iccid, qr_code]):
                print("⚠️ No eSIM details provided to update")
                return

            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Build dynamic UPDATE query based on provided values
                        update_parts = []
                        params = []
                        
                        if phone_number:
                            update_parts.append("phone_number = %s")
                            params.append(phone_number)
                        if lpa_address:
                            update_parts.append("esim_lpa_address = %s")
                            params.append(lpa_address)
                        if iccid:
                            update_parts.append("esim_iccid = %s")
                            params.append(iccid)
                        if qr_code:
                            update_parts.append("esim_qr_code = %s")
                            params.append(qr_code)
                        
                        params.append(firebase_uid)
                        
                        update_query = f"""
                            UPDATE users SET {', '.join(update_parts)}
                            WHERE firebase_uid = %s
                        """
                        
                        cur.execute(update_query, params)
                        conn.commit()
                        
                        print(f"✅ Updated user eSIM details for {firebase_uid}: phone={phone_number}, LPA={lpa_address[:30] if lpa_address else None}..., ICCID={iccid}")

        except Exception as e:
            print(f"❌ Error updating user eSIM details: {str(e)}")

    def _award_purchase_tokens(self, eth_address: str, purchase_amount: int) -> Dict[str, Any]:
        """Award 10.33% DOTM tokens for purchase"""
        try:
            if not eth_address or purchase_amount <= 0:
                return {'success': False, 'message': 'No ETH address or invalid amount'}

            from ethereum_helper import reward_data_purchase

            success, tx_hash = reward_data_purchase(eth_address, purchase_amount)

            if success:
                reward_amount = (purchase_amount / 100) * 0.1033
                print(f"🪙 Awarded {reward_amount:.4f} DOTM tokens to {eth_address}: {tx_hash}")
                return {
                    'success': True,
                    'tx_hash': tx_hash,
                    'reward_amount_usd': reward_amount,
                    'eth_address': eth_address
                }
            else:
                print(f"❌ Failed to award tokens: {tx_hash}")
                return {'success': False, 'error': tx_hash}

        except Exception as e:
            print(f"❌ Error awarding tokens: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _send_activation_email(self, user_email: str, user_name: str, 
                              esim_data: Dict[str, Any], oxio_user_id: str) -> bool:
        """Send eSIM activation confirmation email using database template"""
        try:
            from email_service import send_email

            # Get email template from database
            template_data = self._get_email_template('activation')

            if not template_data:
                # Fallback to default template
                subject = "🎉 Your eSIM is Ready - DOTM Platform"
                html_body = self._get_default_activation_template()
            else:
                subject = template_data['subject']
                html_body = template_data['content']

            # Replace template variables
            variables = {
                'user_name': user_name or 'Valued Customer',
                'user_email': user_email,
                'phone_number': esim_data.get('phone_number', 'Assigned by carrier'),
                'line_id': esim_data.get('line_id', 'System assigned'),
                'iccid': esim_data.get('iccid', 'Available in dashboard'),
                'activation_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
                'qr_code_url': esim_data.get('qr_code', ''),
                'activation_url': esim_data.get('activation_url', ''),
                'oxio_user_id': oxio_user_id
            }

            # Replace all variables in subject and content
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                html_body = html_body.replace(f"{{{{{key}}}}}", str(value))

            result = send_email(
                to_email=user_email,
                subject=subject,
                body="eSIM activation complete - check HTML version for details",
                html_body=html_body
            )

            print(f"📧 Sent eSIM activation email to {user_email}")
            return result

        except Exception as e:
            print(f"❌ Error sending activation email: {str(e)}")
            return False

    def _get_email_template(self, template_type: str) -> Optional[Dict[str, str]]:
        """Get email template from database"""
        try:
            from main import get_db_connection

            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT subject, content 
                            FROM email_templates 
                            WHERE template_type = %s AND is_active = TRUE 
                            ORDER BY modified_date DESC 
                            LIMIT 1
                        """, (template_type,))

                        result = cur.fetchone()
                        if result:
                            return {
                                'subject': result[0],
                                'content': result[1]
                            }

            return None

        except Exception as e:
            print(f"❌ Error getting email template: {str(e)}")
            return None

    def _get_default_activation_template(self) -> str:
        """Get default activation email template"""
        return """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .profile-card { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #28a745; }
                .highlight { color: #28a745; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 eSIM Activation Successful!</h1>
                    <p>Your DOTM eSIM is now active</p>
                </div>

                <div class="content">
                    <p>Hello {{user_name}},</p>

                    <div class="profile-card">
                        <h3>📱 Your eSIM Profile Details</h3>
                        <ul>
                            <li><strong>Phone Number:</strong> <span class="highlight">{{phone_number}}</span></li>
                            <li><strong>Line ID:</strong> {{line_id}}</li>
                            <li><strong>ICCID:</strong> {{iccid}}</li>
                            <li><strong>Status:</strong> ✅ <span class="highlight">Active</span></li>
                            <li><strong>Activation Date:</strong> {{activation_date}}</li>
                        </ul>
                    </div>

                    <div style="background: #e3f2fd; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                        <h3>📲 Activate Your eSIM</h3>
                        <p><strong>Scan this QR code on your device:</strong></p>
                        <img src="data:image/png;base64,{{qr_code_url}}" alt="eSIM QR Code" style="max-width: 300px; margin: 10px auto; display: block;" />
                        <p style="margin-top: 15px;"><strong>Or use this LPA code:</strong></p>
                        <div style="background: white; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; margin: 10px 0;">
                            {{activation_url}}
                        </div>
                        <div style="background: #fff3cd; border-radius: 5px; padding: 15px; margin-top: 20px; text-align: left;">
                            <h4 style="margin-top: 0;">📋 Activation Instructions:</h4>
                            <ol style="margin: 10px 0; padding-left: 20px;">
                                <li>Open your device's Settings</li>
                                <li>Go to Cellular/Mobile Data → Add eSIM</li>
                                <li>Scan the QR code above or enter the LPA code manually</li>
                                <li>Follow on-screen prompts to complete setup</li>
                            </ol>
                            <p style="margin-bottom: 0;"><strong>Note:</strong> Make sure you have an active internet connection (WiFi) during activation.</p>
                        </div>
                    </div>

                    <div style="background: #e9ecef; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <h4>📞 Support</h4>
                        <p>Questions? Contact us at <a href="mailto:support@dotmobile.app">support@dotmobile.app</a></p>
                        <p>Technical ID: {{oxio_user_id}}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

# Create singleton instance
esim_activation_service = eSIMActivationService()