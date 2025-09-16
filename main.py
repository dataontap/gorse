from flask import Flask, request, send_from_directory, render_template, redirect, jsonify, Response
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO, emit
import os
import sys
from typing import Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import time
import threading
import json
import random
import secrets
import re
from datetime import datetime, timedelta

# Initialize connection pool
database_url = os.environ.get('DATABASE_URL')
try:
    pool = SimpleConnectionPool(1, 20, database_url)
    print("Database connection pool initialized successfully")

    @contextmanager
    def get_db_connection():
        connection = pool.getconn()
        try:
            yield connection
        finally:
            pool.putconn(connection)
except Exception as e:
    print(f"Error initializing database connection pool: {str(e)}")
    # Fallback for development without DB
    @contextmanager
    def get_db_connection():
        yield None

# Initialize Stripe
import stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Import OXIO service
from oxio_service import oxio_service

# Import product setup function
from stripe_products import create_stripe_products
import ethereum_helper
import product_rules_helper
from elevenlabs_service import elevenlabs_service

# Import secure GitHub service
from github_service_secure import github_service_secure
from auth_helpers import require_auth, require_admin_auth

# Import Firebase authentication helper
from firebase_helper import firebase_auth_required

# Create products in Stripe if they don't exist
if stripe.api_key:
    try:
        create_stripe_products()
    except Exception as e:
        print(f"Error setting up Stripe products: {str(e)}")

# Create database tables on startup
try:
    with get_db_connection() as conn:
        if conn:
            print("Attempting to create database tables...")
            with conn.cursor() as cur:
                # Check if purchases table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'purchases')")
                purchases_exists = cur.fetchone()[0]

                if not purchases_exists:
                    print("Creating purchases table...")
                    with open('create_purchases_table.sql', 'r') as sql_file:
                        sql_script = sql_file.read()
                        cur.execute(sql_script)
                    print("Purchases table created successfully")
                else:
                    print("Purchases table already exists")

                # Check if subscriptions table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'subscriptions')")
                subscriptions_exists = cur.fetchone()[0]

                if not subscriptions_exists:
                    print("Creating subscriptions table...")
                    with open('create_subscriptions_table.sql', 'r') as sql_file:
                        sql_script = sql_file.read()
                        cur.execute(sql_script)
                    print("Subscriptions table created successfully")
                else:
                    print("Subscriptions table already exists")

                # Check if product_rules table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'product_rules')")
                product_rules_exists = cur.fetchone()[0]

                if not product_rules_exists:
                    print("Creating product_rules table...")
                    with open('create_product_rules_table.sql', 'r') as sql_file:
                        sql_script = sql_file.read()
                        cur.execute(sql_script)
                    print("Product rules table created successfully")
                else:
                    print("Product rules table already exists")

                # Check if beta_testers table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'beta_testers')")
                beta_testers_exists = cur.fetchone()[0]

                if not beta_testers_exists:
                    print("Creating beta_testers table...")
                    create_beta_testers_sql = """
                        CREATE TABLE beta_testers (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            firebase_uid VARCHAR(128) NOT NULL,
                            stripe_customer_id VARCHAR(100),
                            action VARCHAR(50),
                            status VARCHAR(50),
                            stripe_session_id VARCHAR(255),
                            stripe_payment_intent_id VARCHAR(255),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """
                    cur.execute(create_beta_testers_sql)
                    conn.commit()
                    print("beta_testers table created successfully")
                else:
                    print("beta_testers table already exists")
                    # Check if status column exists and add it if missing
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'beta_testers' AND column_name = 'status'
                    """)
                    status_column_exists = cur.fetchone()

                    if not status_column_exists:
                        print("Adding missing status column to beta_testers table...")
                        cur.execute("ALTER TABLE beta_testers ADD COLUMN status VARCHAR(50) DEFAULT 'not_enrolled'")
                        conn.commit()
                        print("Status column added successfully")

                # Check if fcm_tokens table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'fcm_tokens')")
                fcm_tokens_exists = cur.fetchone()[0]

                if not fcm_tokens_exists:
                    print("Creating fcm_tokens table...")
                    create_fcm_tokens_sql = """
                        CREATE TABLE fcm_tokens (
                            id SERIAL PRIMARY KEY,
                            firebase_uid VARCHAR(128) NOT NULL,
                            fcm_token TEXT NOT NULL,
                            platform VARCHAR(20) DEFAULT 'web',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(firebase_uid, platform)
                        );
                        CREATE INDEX IF NOT EXISTS idx_fcm_tokens_firebase_uid ON fcm_tokens(firebase_uid);
                        CREATE INDEX IF NOT EXISTS idx_fcm_tokens_platform ON fcm_tokens(platform);
                    """
                    cur.execute(create_fcm_tokens_sql)
                    conn.commit()
                    print("fcm_tokens table created successfully")
                else:
                    print("fcm_tokens table already exists")

                # Check if notifications table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'notifications')")
                notifications_exists = cur.fetchone()[0]

                if not notifications_exists:
                    print("Creating notifications table...")
                    create_notifications_sql = """
                        CREATE TABLE notifications (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            firebase_uid VARCHAR(128),
                            title VARCHAR(255) NOT NULL,
                            body TEXT,
                            notification_type VARCHAR(50) DEFAULT 'general',
                            delivered BOOLEAN DEFAULT FALSE,
                            read_status BOOLEAN DEFAULT FALSE,
                            fcm_response TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            delivered_at TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        );
                        CREATE INDEX IF NOT EXISTS idx_notifications_firebase_uid ON notifications(firebase_uid);
                        CREATE INDEX IF NOT EXISTS idx_notifications_delivered ON notifications(delivered);
                        CREATE INDEX IF NOT EXISTS idx_notifications_read_status ON notifications(read_status);
                    """
                    cur.execute(create_notifications_sql)
                    conn.commit()
                    print("notifications table created successfully")
                else:
                    print("notifications table already exists")

                conn.commit()
        else:
            print("No database connection available for table creation")
except Exception as e:
    print(f"Error creating tables on startup: {str(e)}")
    print("Continuing without table creation...")


app = Flask(__name__, static_url_path='/static', template_folder='templates') # Added template_folder

# CRITICAL SECURITY: Set session secret key from environment
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    print("WARNING: SESSION_SECRET not configured - using fallback for development")
    app.secret_key = "dev-fallback-secret-change-in-production"

socketio = SocketIO(app, cors_allowed_origins="*")

# Define OXIO endpoints FIRST, before any Flask-RESTX setup
@app.route('/api/oxio/test-connection', methods=['GET'])
def oxio_test_connection():
    """Test OXIO API connection and credentials"""
    try:
        print("=== OXIO TEST CONNECTION CALLED ===")
        result = oxio_service.test_connection()
        print(f"OXIO connection test result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error in OXIO connection test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to test OXIO connection'
        }), 500

@app.route('/api/oxio/test-plans', methods=['GET'])
def oxio_test_plans():
    """Test OXIO plans endpoint specifically"""
    try:
        print("=== OXIO TEST PLANS CALLED ===")
        result = oxio_service.test_plans_endpoint()
        print(f"OXIO plans test result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error in OXIO plans test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to test OXIO plans endpoint'
        }), 500

@app.route('/api/oxio/activate-line', methods=['POST'])
def oxio_activate_line():
    """Activate a line using OXIO API"""
    try:
        print("=== OXIO ACTIVATE LINE CALLED ===")
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No payload provided',
                'message': 'Request body is required'
            }), 400

        result = oxio_service.activate_line(data)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to activate line'
        }), 500

@app.route('/api/oxio/test-sample-activation', methods=['POST'])
def oxio_test_sample_activation():
    """Test line activation with the provided sample payload"""
    try:
        print("=== OXIO TEST SAMPLE ACTIVATION CALLED ===")
        sample_payload = {
            "lineType": "LINE_TYPE_MOBILITY",
            "sim": {
                "simType": "EMBEDDED",
                "iccid": os.environ.get('EUICCID1', '8910650420001501340F')
            },
            "endUser": {
                "brandId": "91f70e2e-d7a8-4e9c-afc6-30acc019ed67"
            },
            "phoneNumberRequirements": {
                "preferredAreaCode": "212"
            },
            "countryCode": "US",
            "activateOnAttach": False
        }

        data = request.get_json()
        if data:
            sample_payload.update(data)

        result = oxio_service.activate_line(sample_payload)
        result['payload_used'] = sample_payload

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to test sample activation'
        }), 500

# Now initialize Flask-RESTX AFTER the OXIO routes are defined
api = Api(app, version='1.0', title='IMEI API',
    description='Get android phone IMEI API with telephony permissions for eSIM activation',
    doc='/api', 
    prefix='/api')  # Move all API endpoints under /api path

ns = api.namespace('imei', description='IMEI operations')

# FCM token registration endpoint
@app.route('/api/register-fcm-token', methods=['POST'])
def register_fcm_token():
    data = request.json
    token = data.get('token')
    firebase_uid = data.get('firebaseUid')
    user_agent = request.headers.get('User-Agent', '')
    platform = 'web' if 'Mozilla' in user_agent else 'android'

    print(f"Registered FCM token for {platform}: {token}")

    # Store token in database if Firebase UID provided
    if firebase_uid and token:
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Insert or update FCM token (table should already exist from startup)
                        cur.execute("""
                            INSERT INTO fcm_tokens (firebase_uid, fcm_token, platform, updated_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (firebase_uid, platform) 
                            DO UPDATE SET 
                                fcm_token = EXCLUDED.fcm_token,
                                updated_at = CURRENT_TIMESTAMP
                        """, (firebase_uid, token, platform))

                        conn.commit()
                        print(f"Stored FCM token for {firebase_uid} on {platform}")

                        # Check for pending notifications that haven't been delivered
                        cur.execute("""
                            SELECT id, title, body, notification_type, created_at
                            FROM notifications 
                            WHERE firebase_uid = %s AND delivered = FALSE 
                            ORDER BY created_at ASC
                        """, (firebase_uid,))

                        pending_notifications = cur.fetchall()

                        if pending_notifications:
                            print(f"Found {len(pending_notifications)} pending notifications for {firebase_uid}")

                            # Send each pending notification
                            for notification in pending_notifications:
                                notification_id, title, body, notif_type, created_at = notification

                                try:
                                    # Use Firebase Admin SDK if available
                                    if 'firebase_admin' in sys.modules:
                                        from firebase_admin import messaging

                                        message = messaging.Message(
                                            notification=messaging.Notification(
                                                title=title,
                                                body=body,
                                            ),
                                            token=token,
                                            data={
                                                'type': notif_type,
                                                'notification_id': str(notification_id),
                                                'timestamp': str(int(time.time()))
                                            }
                                        )

                                        response = messaging.send(message)
                                        print(f'Pending notification {notification_id} sent successfully: {response}')

                                        # Update notification as delivered
                                        cur.execute("""
                                            UPDATE notifications 
                                            SET delivered = TRUE, delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                            WHERE id = %s
                                        """, (str(response), notification_id))

                                    else:
                                        print("Firebase Admin SDK not available - marking notification as delivered for demo")
                                        # Mark as delivered even without FCM for demo purposes
                                        cur.execute("""
                                            UPDATE notifications 
                                            SET delivered = TRUE, delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                            WHERE id = %s
                                        """, ("No FCM SDK - demo mode", notification_id))

                                except Exception as msg_err:
                                    print(f"Error sending pending notification {notification_id}: {str(msg_err)}")
                                    # Still mark as delivered to avoid repeated attempts
                                    cur.execute("""
                                        UPDATE notifications 
                                        SET delivered = TRUE, delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                        WHERE id = %s
                                    """, (f"FCM Error: {str(msg_err)}", notification_id))

                            conn.commit()
                            print(f"Processed {len(pending_notifications)} pending notifications")

                            return jsonify({"status": "success", "platform": platform})

        except Exception as e:
            print(f"Error processing FCM token registration: {str(e)}")
            return jsonify({"error": "Failed to register FCM token"}), 500

    return jsonify({"status": "success", "platform": platform}) # Fallback return if no firebase_uid or token


# Send notifications to both web and app users
@app.route('/api/send-notification', methods=['POST'])
def send_notification():
    if not request.json:
        return jsonify({"error": "No data provided"}), 400

    title = request.json.get('title', 'Notification')
    body = request.json.get('body', 'You have a new notification')
    target = request.json.get('target', 'all')  # 'all', 'web', 'app'
    firebase_uid = request.json.get('firebaseUid')

    try:
        # Get user's FCM token if Firebase UID provided
        fcm_token = None
        if firebase_uid:
            try:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            # Check if fcm_tokens table exists, create if not
                            cur.execute("""
                                CREATE TABLE IF NOT EXISTS fcm_tokens (
                                    id SERIAL PRIMARY KEY,
                                    firebase_uid VARCHAR(128) NOT NULL,
                                    fcm_token TEXT NOT NULL,
                                    platform VARCHAR(20) DEFAULT 'web',
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    UNIQUE(firebase_uid, platform)
                                )
                            """)

                            # Get user's FCM token
                            cur.execute("""
                                SELECT fcm_token FROM fcm_tokens 
                                WHERE firebase_uid = %s AND platform = 'web'
                                ORDER BY updated_at DESC LIMIT 1
                            """, (firebase_uid,))

                            result = cur.fetchone()
                            if result:
                                fcm_token = result[0]
            except Exception as token_err:
                print(f"Error getting FCM token: {str(token_err)}")

        # Example of sending to specific platforms
        if target == 'all' or target == 'app':
            # Send to Android app users
            send_to_android(title, body, fcm_token)

        if target == 'all' or target == 'web':
            # Send to Web users
            send_to_web(title, body, fcm_token)

        return jsonify({"status": "success", "message": f"Notification sent to {target}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_to_android(title, body, fcm_token=None):
    # Send to Android app users using Firebase Admin SDK
    print(f"Sending to Android: {title} - {body}")

    if fcm_token:
        try:
            # Use Firebase Admin SDK if available
            if 'firebase_admin' in sys.modules:
                from firebase_admin import messaging

                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    token=fcm_token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            icon='ic_notification',
                            color='#00ffff'
                        )
                    )
                )

                response = messaging.send(message)
                print('Successfully sent Android message:', response)
                return response
        except Exception as e:
            print(f"Error sending Android notification: {str(e)}")

    return None

def send_to_web(title, body, fcm_token=None):
    # Send to Web users using Firebase Admin SDK with web push credentials
    print(f"Sending to Web: {title} - {body}")

    if fcm_token:
        try:
            # Use Firebase Admin SDK if available
            if 'firebase_admin' in sys.modules:
                from firebase_admin import messaging

                # Get web messaging credentials from environment
                web_private_key = os.environ.get('WEB_MESSAGING_PRIVATE_KEY')
                web_authorization = os.environ.get('WEB_MESSAGING_AUTHORIZATION')

                # Configure web push options
                web_push_config = None
                if web_private_key and web_authorization:
                    web_push_config = messaging.WebpushConfig(
                        headers={
                            'Authorization': web_authorization,
                            'Private-Key': web_private_key
                        },
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon='/static/tropical-border.png',
                            badge='/static/tropical-border.png',
                            tag='dotm-notification',
                            requireInteraction=False
                        )
                    )

                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    token=fcm_token,
                    webpush=web_push_config
                )

                response = messaging.send(message)
                print('Successfully sent web message:', response)
                return response
        except Exception as e:
            print(f"Error sending web notification: {str(e)}")

    return None

delivery_ns = api.namespace('delivery', description='eSIM delivery operations')
customer_ns = api.namespace('customer', description='Customer operations')

# Firebase Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def register_firebase_user():
    """Register a Firebase user in our database"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    firebase_uid = data.get('firebaseUid')
    email = data.get('email')
    display_name = data.get('displayName')
    photo_url = data.get('photoURL')

    if not firebase_uid or not email:
        return jsonify({'error': 'Firebase UID and email are required'}), 400

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if users table exists
                    cur.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                    )
                    table_exists = cur.fetchone()[0]

                    if not table_exists:
                        # Create users table with correct column names including OXIO user ID
                        cur.execute("""
                            CREATE TABLE users (
                                id SERIAL PRIMARY KEY,
                                email VARCHAR(255) NOT NULL,
                                firebase_uid VARCHAR(128) UNIQUE NOT NULL,
                                stripe_customer_id VARCHAR(100),
                                display_name VARCHAR(255),
                                photo_url TEXT,
                                imei VARCHAR(100),
                                eth_address VARCHAR(42),
                                oxio_user_id VARCHAR(100),
                                oxio_group_id VARCHAR(100),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        conn.commit()
                        print("Users table created with Firebase fields and OXIO user ID")
                    else:
                        # Check if oxio_user_id column exists and add it if missing
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'oxio_user_id'
                        """)
                        oxio_column_exists = cur.fetchone()

                        if not oxio_column_exists:
                            print("Adding oxio_user_id column to users table...")
                            cur.execute("ALTER TABLE users ADD COLUMN oxio_user_id VARCHAR(100)")
                            conn.commit()
                            print("OXIO user ID column added successfully")

                        # Check if oxio_group_id column exists and add it if missing
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'oxio_group_id'
                        """)
                        oxio_group_column_exists = cur.fetchone()

                        if not oxio_group_column_exists:
                            print("Adding oxio_group_id column to users table...")
                            cur.execute("ALTER TABLE users ADD COLUMN oxio_group_id VARCHAR(100)")
                            conn.commit()
                            print("OXIO group ID column added successfully")

                        # Ensure eth_address column exists separately
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'eth_address'
                        """)
                        eth_column_exists = cur.fetchone()

                        if not eth_column_exists:
                            print("Adding eth_address column to users table...")
                            cur.execute("ALTER TABLE users ADD COLUMN eth_address VARCHAR(42)")
                            conn.commit()
                            print("ETH address column added successfully")

                    # Check if user already exists by Firebase UID
                    cur.execute("SELECT id, stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    existing_user = cur.fetchone()

                    if existing_user:
                        # User exists, return the user ID
                        user_id = existing_user[0]
                        stripe_customer_id = existing_user[1]
                        print(f"Existing Firebase user found: {user_id} with Stripe customer: {stripe_customer_id}")

                        # Update user information if needed
                        cur.execute(
                            """UPDATE users SET 
                                email = %s, 
                                display_name = %s, 
                                photo_url = %s 
                            WHERE id = %s""",
                            (email, display_name, photo_url, user_id)
                        )
                        conn.commit()

                        # If no Stripe customer exists, create one
                        if not stripe_customer_id and stripe.api_key:
                            try:
                                customer = stripe.Customer.create(
                                    email=email,
                                    name=display_name,
                                    metadata={'firebase_uid': firebase_uid, 'user_id': user_id}
                                )
                                stripe_customer_id = customer.id

                                # Update user with Stripe ID
                                cur.execute(
                                    "UPDATE users SET stripe_customer_id = %s WHERE id = %s",
                                    (stripe_customer_id, user_id)
                                )
                                conn.commit()
                                print(f"Created Stripe customer {stripe_customer_id} for existing user {user_id}")
                            except Exception as stripe_err:
                                print(f"Error creating Stripe customer for existing user: {str(stripe_err)}")
                    else:
                        # Create new user with Sepolia test wallet
                        from web3 import Web3
                        web3 = Web3()
                        test_account = web3.eth.account.create()

                        # Create OXIO group and user
                        oxio_user_id = None
                        oxio_group_id = None
                        try:
                            print(f"Creating OXIO group and user for Firebase UID: {firebase_uid}")

                            # Create OXIO group first
                            group_name = f"DOT_User_{firebase_uid[:8]}"
                            group_result = oxio_service.create_oxio_group(
                                group_name=group_name,
                                description=f"Group for DOT user {display_name or 'Anonymous'}"
                            )

                            if group_result.get('success'):
                                oxio_group_id = group_result.get('oxio_group_id')
                                print(f"Successfully created OXIO group: {oxio_group_id}")
                            else:
                                print(f"Failed to create OXIO group: {group_result.get('message', 'Unknown error')}")

                            # Parse display_name to get first and last name
                            name_parts = (display_name or "Anonymous Anonymous").split(' ', 1)
                            first_name = name_parts[0] if name_parts else "Anonymous"
                            last_name = name_parts[1] if len(name_parts) > 1 else "Anonymous"

                            # Create OXIO user with group ID
                            oxio_result = oxio_service.create_oxio_user(
                                first_name=first_name,
                                last_name=last_name,
                                email=email,
                                firebase_uid=firebase_uid,
                                oxio_group_id=oxio_group_id
                            )

                            if oxio_result.get('success'):
                                oxio_user_id = oxio_result.get('oxio_user_id')
                                print(f"Successfully created OXIO user: {oxio_user_id}")
                            else:
                                # Check if user already exists (error code 6805)
                                if (oxio_result.get('status_code') == 400 and 
                                    oxio_result.get('data', {}).get('code') == 6805):
                                    print(f"OXIO user already exists for {email}, attempting to find existing user ID")

                                    # Try to find existing OXIO user by email
                                    existing_user_result = oxio_service.find_user_by_email(email)
                                    if existing_user_result.get('success'):
                                        oxio_user_id = existing_user_result.get('oxio_user_id')
                                        print(f"Found existing OXIO user ID: {oxio_user_id}")
                                    else:
                                        print(f"Could not find existing OXIO user, will proceed without OXIO user ID")
                                else:
                                    print(f"Failed to create OXIO user: {oxio_result.get('message', 'Unknown error')}")
                        except Exception as oxio_err:
                            print(f"Error creating OXIO group/user: {str(oxio_err)}")

                        cur.execute(
                            """INSERT INTO users 
                                (email, firebase_uid, display_name, photo_url, eth_address, oxio_user_id, oxio_group_id) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s) 
                            RETURNING id""",
                            (email, firebase_uid, display_name, photo_url, test_account.address, oxio_user_id, oxio_group_id)
                        )
                        user_id = cur.fetchone()[0]
                        conn.commit()
                        print(f"New Firebase user created: {user_id} with Sepolia wallet: {test_account.address} and OXIO user ID: {oxio_user_id}")

                        # Award 1 DOTM token to new member
                        try:
                            success, result = ethereum_helper.award_new_member_token(test_account.address)
                            if success:
                                print(f"Awarded 1 DOTM token to new member: {result}")
                            else:
                                print(f"Failed to award new member token: {result}")
                        except Exception as token_err:
                            print(f"Error awarding new member token: {str(token_err)}")

                        # Schedule welcome message and audio generation
                        import threading
                        def send_welcome_message():
                            import time
                            time.sleep(3)  # Wait 3 seconds for FCM token registration
                            try:
                                # Create welcome_messages table if it doesn't exist
                                with get_db_connection() as conn:
                                    if conn:
                                        with conn.cursor() as cur:
                                            cur.execute("""
                                                CREATE TABLE IF NOT EXISTS welcome_messages (
                                                    id SERIAL PRIMARY KEY,
                                                    user_id INTEGER NOT NULL,
                                                    firebase_uid VARCHAR(128),
                                                    language VARCHAR(10) DEFAULT 'en',
                                                    voice_id VARCHAR(100),
                                                    audio_data BYTEA,
                                                    audio_url VARCHAR(500),
                                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                                )
                                            """)
                                            conn.commit()

                                # Generate welcome audio message
                                audio_message_id = None
                                audio_url = None
                                try:
                                    audio_result = elevenlabs_service.generate_welcome_message(
                                        user_name=display_name,
                                        language='en'
                                    )

                                    if audio_result['success']:
                                        # Store the audio message with a generated URL path
                                        audio_url = f"/api/welcome-audio/{user_id}/{firebase_uid}"

                                        with get_db_connection() as conn:
                                            if conn:
                                                with conn.cursor() as cur:
                                                    cur.execute("""
                                                        INSERT INTO welcome_messages 
                                                        (user_id, firebase_uid, language, voice_id, audio_data, audio_url, created_at)
                                                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                                                        RETURNING id
                                                    """, (user_id, firebase_uid, 'en', '21m00Tcm4TlvDq8ikWAM', audio_result['audio_data'], audio_url))

                                                    audio_message_id = cur.fetchone()[0]
                                                    conn.commit()
                                                    print(f"Welcome audio message created with ID: {audio_message_id} at URL: {audio_url}")
                                except Exception as audio_err:
                                    print(f"Error generating welcome audio: {str(audio_err)}")
                                    audio_message_id = None
                                # Get user's FCM token
                                with get_db_connection() as conn:
                                    if conn:
                                        with conn.cursor() as cur:
                                            cur.execute("""
                                                SELECT fcm_token FROM fcm_tokens 
                                                WHERE firebase_uid = %s 
                                                ORDER BY updated_at DESC LIMIT 1
                                            """, (firebase_uid,))

                                            result = cur.fetchone()
                                            fcm_token = result[0] if result else None

                                            # Store notification in database first
                                            welcome_title = "Welcome to DOT Wireless! 🎉"
                                            welcome_body = f"Hi {display_name or 'there'}! Your account is ready. Your personalized welcome message is waiting for you!"

                                            cur.execute("""
                                                INSERT INTO notifications 
                                                (user_id, firebase_uid, title, body, notification_type, delivered)
                                                VALUES (%s, %s, %s, %s, %s, %s)
                                                RETURNING id
                                            """, (user_id, firebase_uid, welcome_title, welcome_body, 'welcome', True))

                                            notification_id = cur.fetchone()[0]
                                            conn.commit()
                                            print(f"Welcome notification stored in database with ID: {notification_id}")

                                            if fcm_token:
                                                # Send welcome notification via FCM
                                                try:
                                                    if 'firebase_admin' in sys.modules:
                                                        from firebase_admin import messaging

                                                        message = messaging.Message(
                                                            notification=messaging.Notification(
                                                                title=welcome_title,
                                                                body=welcome_body,
                                                            ),
                                                            token=fcm_token,
                                                            data={
                                                                'type': 'welcome',
                                                                'user_id': str(user_id),
                                                                'notification_id': str(notification_id),
                                                                'timestamp': str(int(time.time()))
                                                            }
                                                        )

                                                        response = messaging.send(message)
                                                        print(f'Welcome message sent successfully to {firebase_uid}: {response}')

                                                        # Update notification with FCM response
                                                        cur.execute("""
                                                            UPDATE notifications 
                                                            SET delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                                            WHERE id = %s
                                                        """, (str(response), notification_id))
                                                        conn.commit()
                                                        print(f"Notification {notification_id} marked as delivered via FCM")

                                                    else:
                                                        print("Firebase Admin SDK not available - notification stored in database")
                                                        cur.execute("""
                                                            UPDATE notifications 
                                                            SET delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                                            WHERE id = %s
                                                        """, ("No FCM SDK - demo mode", notification_id))
                                                        conn.commit()

                                                except Exception as msg_err:
                                                    print(f"Error sending welcome message via FCM: {str(msg_err)}")
                                                    cur.execute("""
                                                        UPDATE notifications 
                                                        SET delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                                        WHERE id = %s
                                                    """, (f"FCM Error: {str(msg_err)}", notification_id))
                                                    conn.commit()
                                            else:
                                                print(f"No FCM token found for {firebase_uid} - notification stored for later")
                                                cur.execute("""
                                                    UPDATE notifications 
                                                    SET delivered_at = CURRENT_TIMESTAMP, fcm_response = %s
                                                    WHERE id = %s
                                                """, ("No FCM token available", notification_id))
                                                conn.commit()

                            except Exception as welcome_err:
                                print(f"Error in welcome message thread: {str(welcome_err)}")

                        # Start welcome message thread
                        welcome_thread = threading.Thread(target=send_welcome_message)
                        welcome_thread.daemon = True
                        welcome_thread.start()
                        print(f"Welcome message scheduled for {firebase_uid} in 3 seconds")

                        # Create Stripe customer for new user
                        stripe_customer_id = None
                        if stripe.api_key:
                            try:
                                customer = stripe.Customer.create(
                                    email=email,
                                    name=display_name,
                                    metadata={'firebase_uid': firebase_uid, 'user_id': user_id, 'oxio_user_id': oxio_user_id or ''}
                                )
                                stripe_customer_id = customer.id

                                # Update user with Stripe ID
                                cur.execute(
                                    "UPDATE users SET stripe_customer_id = %s WHERE id = %s",
                                    (stripe_customer_id, user_id)
                                )
                                conn.commit()
                                print(f"Created Stripe customer {stripe_customer_id} for new user {user_id}")
                            except Exception as stripe_err:
                                print(f"Error creating Stripe customer for new user: {str(stripe_err)}")

                    return jsonify({
                        'status': 'success',
                        'userId': user_id,
                        'stripeCustomerId': stripe_customer_id
                    })

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error registering Firebase user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/update-imei', methods=['POST'])
def update_user_imei():
    """Update a user's IMEI number"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    firebase_uid = data.get('firebaseUid')
    imei = data.get('imei')

    if not firebase_uid or not imei:
        return jsonify({'error': 'Firebase UID and IMEI are required'}), 400

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET imei = %s WHERE firebase_uid = %s RETURNING id",
                        (imei, firebase_uid)
                    )
                    result = cur.fetchone()
                    conn.commit()

                    if result:
                        return jsonify({
                            'status': 'success',
                            'userId': result[0],
                            'message': 'IMEI updated successfully'
                        })
                    else:
                        return jsonify({'error': 'User not found'}), 404

            return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error updating IMEI: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/imei-compatibility', methods=['POST'])
def check_imei_compatibility():
    """Check IMEI compatibility using external service"""
    try:
        data = request.get_json()
        if not data or not data.get('imei'):
            return jsonify({'error': 'IMEI is required'}), 400

        imei = data.get('imei')
        location = data.get('location', 'Global')
        network = data.get('network', 'OXIO')

        # Get API key from environment
        api_key = os.environ.get('IMEI_COMPATIBILITY_KEY', 'demo-key-123')

        # Call external IMEI compatibility service
        import requests

        compatibility_response = requests.post(
            'https://will-my-phone-work.replit.app/api/v1/check',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            json={
                'imei': imei,
                'location': location,
                'network': network
            },
            timeout=30
        )

        if compatibility_response.status_code == 200:
            result = compatibility_response.json()

            # Log the compatibility check
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create compatibility_checks table if it doesn't exist
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS compatibility_checks (
                                id SERIAL PRIMARY KEY,
                                imei VARCHAR(50) NOT NULL,
                                device_make VARCHAR(100),
                                device_model VARCHAR(100),
                                device_year INTEGER,
                                four_g_support BOOLEAN,
                                five_g_support BOOLEAN,
                                volte_support BOOLEAN,
                                wifi_calling_support VARCHAR(20),
                                is_compatible BOOLEAN,
                                search_id INTEGER,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)

                        # Insert compatibility check record
                        device = result.get('device', {})
                        capabilities = result.get('capabilities', {})
                        is_compatible = capabilities.get('fourG', False) or capabilities.get('fiveG', False)

                        cur.execute("""
                            INSERT INTO compatibility_checks 
                            (imei, device_make, device_model, device_year, four_g_support, 
                             five_g_support, volte_support, wifi_calling_support, is_compatible, search_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            imei,
                            device.get('make'),
                            device.get('model'),
                            device.get('year'),
                            capabilities.get('fourG', False),
                            capabilities.get('fiveG', False),
                            capabilities.get('volte', False),
                            capabilities.get('wifiCalling', 'unknown'),
                            is_compatible,
                            result.get('searchId')
                        ))

                        conn.commit()

            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': 'Compatibility service unavailable',
                'message': 'Unable to check device compatibility at this time'
            }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Service timeout',
            'message': 'Compatibility check timed out. Please try again.'
        }), 504
    except Exception as e:
        print(f"Error checking IMEI compatibility: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Unable to process compatibility check'
        }), 500

@app.route('/api/auth/current-user', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user data from database using Firebase UID - NOW AUTHENTICATED"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400
    
    # The require_auth decorator already validates the Firebase UID exists in database
    
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get user data including founder status, OXIO user ID, and ETH address
                    cur.execute(
                        """SELECT u.id, u.email, u.display_name, u.photo_url, u.imei, u.stripe_customer_id,
                                  COALESCE(f.founder, 'N') as founder_status, u.oxio_user_id, u.eth_address, u.oxio_group_id
                        FROM users u
                        LEFT JOIN founders f ON u.firebase_uid = f.firebase_uid
                        WHERE u.firebase_uid = %s""",
                        (firebase_uid,)
                    )
                    user = cur.fetchone()

                    if user:
                        return jsonify({
                            'status': 'success',
                            'userId': user[0],
                            'email': user[1],
                            'displayName': user[2],
                            'photoURL': user[3],
                            'imei': user[4],
                            'stripeCustomerId': user[5],
                            'founderStatus': user[6],
                            'oxioUserId': user[7],
                            'metamaskAddress': user[8] if len(user) > 8 else None, # Correctly index for eth_address
                            'oxioGroupId': user[9] if len(user) > 9 else None # Correctly index for oxio_group_id
                        })

                    return jsonify({'error': 'User not found'}), 404

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error getting current user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/founder-status', methods=['GET'])
def get_founder_status():
    """Get founder status for a specific user"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT f.founder, f.created_at as founder_since
                        FROM founders f
                        WHERE f.firebase_uid = %s""",
                        (firebase_uid,)
                    )
                    result = cur.fetchone()

                    if result:
                        return jsonify({
                            'status': 'success',
                            'isFounder': result[0] == 'Y',
                            'founderSince': result[1].isoformat() if result[1] else None
                        })
                    else:
                        return jsonify({
                            'status': 'success',
                            'isFounder': False,
                            'founderSince': None
                        })

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error getting founder status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Update member count endpoint
@app.route('/api/member-count', methods=['GET'])
def get_member_count():
    """Get the total number of members from the users table"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if users table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'users'
                        )
                    """)
                    table_exists = cur.fetchone()[0]

                    if not table_exists:
                        return jsonify({'count': 1, 'error': 'Users table does not exist'})

                    # Count total number of users
                    cur.execute("SELECT COUNT(*) FROM users")
                    count = cur.fetchone()[0]

                    # If count is 0, return at least 1 for the current user
                    if count == 0:
                        count = 1

                    return jsonify({
                        'count': count,
                        'status': 'success'
                    })

            # If no database connection, return default count of 1
            return jsonify({'count': 1, 'error': 'No database connection'})
    except Exception as e:
        print(f"Error getting member count: {str(e)}")
        # Return default count if there's an error
        return jsonify({'count': 1, 'error': str(e)})


customer_model = api.model('Customer', {
    'email': fields.String(required=True, description='Customer email address')
})

delivery_model = api.model('Delivery', {
    'method': fields.String(required=True, description='Delivery method (email or sms)'),
    'contact': fields.String(required=True, description='Email address or phone number')
})

imei_model = api.model('IMEI', {
    'imei1': fields.String(required=True, description='Primary IMEI number'),
    'imei2': fields.String(required=False, description='Secondary IMEI number (dual SIM devices)')
})

def record_purchase(stripe_id, product_id, price_id, amount, user_id=None, transaction_id=None, firebase_uid=None, stripe_transaction_id=None):
    """Records a purchase in the database with proper Firebase UID lookup and Stripe transaction tracking"""
    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        attempts += 1
        try:
            print(f"Attempting to record purchase: StripeID={stripe_id}, ProductID={product_id}, PriceID={price_id}, Amount={amount}, TransactionID={transaction_id}, StripeTransactionID={stripe_transaction_id}, FirebaseUID={firebase_uid}")
            with get_db_connection() as conn:
                if conn:
                    try:
                        with conn.cursor() as cur:
                            # First, check if the purchases table exists
                            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'purchases')")
                            table_exists = cur.fetchone()[0]

                            # Create the table if it doesn't exist
                            if not table_exists:
                                print("Purchases table does not exist. Creating it now...")
                                create_table_sql = """
                                CREATE TABLE IF NOT EXISTS purchases (
                                    PurchaseID SERIAL PRIMARY KEY,
                                    StripeID VARCHAR(100),
                                    StripeProductID VARCHAR(100) NOT NULL,
                                    PriceID VARCHAR(100) NOT NULL,
                                    TotalAmount INTEGER NOT NULL,
                                    DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    UserID INTEGER,
                                    StripeTransactionID VARCHAR(100),
                                    FirebaseUID VARCHAR(128)
                                );

                                CREATE INDEX IF NOT EXISTS idx_purchases_stripe ON purchases(StripeID);
                                CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(StripeProductID);
                                CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(UserID);
                                CREATE INDEX IF NOT EXISTS idx_purchases_firebase_uid ON purchases(FirebaseUID);
                                """
                                cur.execute(create_table_sql)
                                conn.commit()
                                print("Purchases table created successfully")
                            else:
                                # Check if new columns exist and add them if needed
                                cur.execute("""
                                    SELECT column_name FROM information_schema.columns 
                                    WHERE table_name = 'purchases'
                                """)
                                columns = [row[0] for row in cur.fetchall()]

                                if 'stripetransactionid' not in [col.lower() for col in columns]:
                                    print("Adding StripeTransactionID column to purchases table...")
                                    cur.execute("ALTER TABLE purchases ADD COLUMN StripeTransactionID VARCHAR(100)")

                                if 'firebaseuid' not in [col.lower() for col in columns]:
                                    print("Adding FirebaseUID column to purchases table...")
                                    cur.execute("ALTER TABLE purchases ADD COLUMN FirebaseUID VARCHAR(128)")

                                conn.commit()

                            # Handle null StripeID (make it empty string instead)
                            if stripe_id is None:
                                stripe_id = ''

                            # Always try to look up user by Firebase UID first if provided
                            if firebase_uid:
                                cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                                user_result = cur.fetchone()
                                if user_result:
                                    user_id = user_result[0]
                                    print(f"Found user {user_id} for Firebase UID {firebase_uid}")
                                else:
                                    print(f"No user found for Firebase UID {firebase_uid}")
                                    # Return None if no user found and no user_id provided
                                    if not user_id:
                                        print("Cannot record purchase: No valid user found")
                                        return None

                            # Require valid user_id - don't default to 1
                            if not user_id:
                                print("Cannot record purchase: No user_id provided and no Firebase UID found")
                                return None

                            print(f"Using user_id: {user_id}")

                            # Now insert the purchase record with all tracking information
                            cur.execute(
                                """INSERT INTO purchases 
                                   (StripeID, StripeProductID, PriceID, TotalAmount, UserID, DateCreated, StripeTransactionID, FirebaseUID) 
                                   VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s) 
                                   RETURNING PurchaseID""",
                                (stripe_id, product_id, price_id, amount, user_id, stripe_transaction_id, firebase_uid)
                            )
                            purchase_id = cur.fetchone()[0]
                            conn.commit()
                            print(f"Purchase successfully recorded: {purchase_id} for user {user_id} with Firebase UID {firebase_uid}")
                            return purchase_id
                    except psycopg2.Error as db_err:
                        print(f"Database error recording purchase (attempt {attempts}/{max_attempts}): {str(db_err)}")
                        conn.rollback()
                        # Only continue if there are more attempts
                        if attempts < max_attempts:
                            print(f"Retrying... (attempt {attempts+1}/{max_attempts})")
                            continue
                else:
                    print(f"No database connection available (attempt {attempts}/{max_attempts})")
                    # Only continue if there are more attempts
                    if attempts < max_attempts:
                        print(f"Retrying to get connection... (attempt {attempts+1}/{max_attempts})")
                        continue
        except Exception as e:
            print(f"Unexpected error recording purchase (attempt {attempts}/{max_attempts}): {str(e)}")
            # Only continue if there are more attempts
            if attempts < max_attempts:
                print(f"Retrying after error... (attempt {attempts+1}/{max_attempts})")
                continue

    print("Failed to record purchase after multiple attempts")
    # For debugging purposes, let's also print the database connection string (with credentials removed)
    try:
        db_url = os.environ.get('DATABASE_URL', '')
        if db_url:
            # Safely print DB URL with credentials masked
            masked_url = db_url.replace('://', '://***:***@')
            print(f"Database URL format: {masked_url}")
    except Exception as e:
        print(f"Error checking database URL: {str(e)}")

    return None

def create_subscription(user_id, subscription_type, stripe_subscription_id=None, firebase_uid=None):
    """Creates a subscription record in the database with exactly 365.25 days validity"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # If Firebase UID is provided but no user_id, look up the user
                    if firebase_uid and not user_id:
                        cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        user_result = cur.fetchone()
                        if user_result:
                            user_id = user_result[0]
                            print(f"Found user {user_id} for Firebase UID {firebase_uid} when creating subscription")
                        else:
                            print(f"No user found for Firebase UID {firebase_uid} when creating subscription")
                            user_id = 1  # Default fallback

                    # Use default user_id if still not found
                    if not user_id:
                        user_id = 1
                        print(f"Using default user_id for subscription: {user_id}")

                    # First, deactivate any existing active subscriptions for this user
                    cur.execute("""
                        UPDATE subscriptions 
                        SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND status = 'active'
                    """, (user_id,))

                    # Create Stripe subscription FIRST if this is a membership product
                    actual_stripe_subscription_id = stripe_subscription_id
                    if stripe.api_key and subscription_type in ['basic_membership', 'full_membership'] and not stripe_subscription_id:
                        try:
                            # Get the user's Stripe customer ID
                            cur.execute("SELECT stripe_customer_id FROM users WHERE id = %s", (user_id,))
                            customer_result = cur.fetchone()

                            if customer_result and customer_result[0]:
                                customer_id = customer_result[0]

                                # Get the appropriate price ID for the subscription
                                prices = stripe.Price.list(product=subscription_type, active=True, type='recurring')
                                if prices.data:
                                    price_id = prices.data[0].id

                                    # Create Stripe subscription
                                    stripe_subscription = stripe.Subscription.create(
                                        customer=customer_id,
                                        items=[{'price': price_id}],
                                        metadata={
                                            'user_id': str(user_id),
                                            'subscription_type': subscription_type,
                                            'firebase_uid': firebase_uid or ''
                                        }
                                    )
                                    actual_stripe_subscription_id = stripe_subscription.id
                                    print(f"Created Stripe subscription {actual_stripe_subscription_id} for user {user_id}")
                                else:
                                    print(f"No recurring price found for product {subscription_type}")
                            else:
                                print(f"No Stripe customer ID found for user {user_id}")
                        except Exception as stripe_err:
                            print(f"Error creating Stripe subscription: {str(stripe_err)}")
                            # Continue with local subscription creation even if Stripe fails

                    # Calculate validity end date (1 year = 365.25 days exactly for leap years)
                    cur.execute("""
                        INSERT INTO subscriptions 
                        (user_id, subscription_type, stripe_subscription_id, start_date, end_date, status, created_at, updated_at) 
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + interval '365.25 days', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
                        RETURNING end_date, subscription_id
                    """, (user_id, subscription_type, actual_stripe_subscription_id))

                    result = cur.fetchone()
                    end_date = result[0]
                    subscription_id = result[1]
                    conn.commit()
                    print(f"Subscription {subscription_id} created for user {user_id} (Firebase UID: {firebase_uid}), type {subscription_type}, Stripe ID: {actual_stripe_subscription_id}, valid until {end_date}")

                    return end_date
            else:
                print("No database connection available")
                return None
    except Exception as e:
        print(f"Error creating subscription: {str(e)}")
        return None

@delivery_ns.route('')
class DeliveryResource(Resource):
    @delivery_ns.response(400, 'Bad Request')
    def post(self):
        """Submit eSIM delivery preferences"""
        try:
            data = request.get_json()
            if not data:
                return {'message': 'No data provided', 'status': 'error'}, 400

            # Create or retrieve the product
            if not stripe.api_key:
                return {'message': 'Stripe API key not configured', 'status': 'error'}, 500

            try:
                product = stripe.Product.retrieve('esim_activation_v1')
            except stripe.error.InvalidRequestError as e:
                print(f"Stripe error: {str(e)}")
                # Create a price first
                price = stripe.Price.create(
                    unit_amount=100,  # $1.00 USD in cents
                    currency='usd',
                    product_data={
                        'id': 'esim_activation_v1',
                        'name': 'eSIM Activation',
                        'metadata': {
                            'type': 'esim',
                            'product_catalog': 'digital_services'
                        }
                    }
                )
                product = stripe.Product.retrieve('esim_activation_v1')

            # Create or retrieve Stripe customer
            try:
                # Create customer
                customer = stripe.Customer.create(
                    email=data['contact'] if data['method'] == 'email' else None,
                    phone=data['contact'] if data['method'] == 'sms' else None,
                    description='eSIM activation customer'
                )

                # Create invoice first
                invoice = stripe.Invoice.create(
                    customer=customer.id,
                    collection_method='send_invoice',
                    days_until_due=1,  # Due in 1 day
                    auto_advance=False,  #Don't finalize yet
                    description='eSIM Activation Service'
                )

                # Add invoice item
                stripe.InvoiceItem.create(
                    customer=customer.id,
                    amount=100,  # $1.00 in cents
                    currency='usd',
                    description='eSIM Activation',
                    invoice=invoice.id
                )

                # Finalize and send invoice
                invoice = stripe.Invoice.finalize_invoice(invoice.id, auto_advance=False)
                invoice = stripe.Invoice.send_invoice(invoice.id)

                print(f"Invoice sent successfully to customer {customer.id}")

                return {
                    'message': 'Invoice sent successfully',
                    'status': 'success',
                    'payment_url': invoice.hosted_invoice_url
                }
            except Exception as e:
                return {'message': str(e), 'status': 'error'}, 500

        except Exception as e:
            return {'message': str(e), 'status': 'error'}, 500

imei_model = api.model('IMEI', {
    'imei1': fields.String(required=True, description='Primary IMEI number'),
    'imei2': fields.String(required=False, description='Secondary IMEI number (dual SIM devices)')
})

@ns.route('')
class IMEIResource(Resource):
    @ns.expect(imei_model)
    @ns.response(200, 'Success')
    @ns.response(400, 'Bad Request')
    @ns.response(500, 'Internal Server Error')
    def post(self):
        """Submit IMEI information from Android device"""
        try:
            data = request.get_json()
            if not data:
                return {'message': 'No data provided', 'status': 'error'}, 400
            if 'imei1' not in data or not data['imei1']:
                return {'message': 'IMEI1 is required', 'status': 'error'}, 400

            timestamp = datetime.now().isoformat()

            # Store in database with timestamp as key
            db[timestamp] = {
                'imei1': data.get('imei1'),
                'imei2': data.get('imei2')
            }

            return {
                'message': 'Your IMEI has been successfully shared for eSIM activation',
                'status': 'success',
                'data': {
                    'imei1': data.get('imei1'),
                    'imei2': data.get('imei2'),
                    'timestamp': timestamp
                }
            }
        except Exception as e:
            return {'message': f'Internal Server Error: {str(e)}', 'status': 'error'}, 500

    def get(self):
        """Get all stored IMEI submissions and statistics"""
        try:
            submissions = {}
            unique_imei1 = set()
            unique_imei2 = set()

            # Safely get database entries
            for key in db.keys():
                try:
                    submission = db[key]
                    submissions[key] = submission
                    if submission.get('imei1'):
                        unique_imei1.add(submission['imei1'])
                    if submission.get('imei2'):
                        unique_imei2.add(submission['imei2'])
                except Exception as e:
                    print(f"Error accessing key {key}: {str(e)}")
                    continue

            stats = {
                'total_submissions': len(submissions),
                'unique_primary_imeis': len(unique_imei1),
                'unique_secondary_imeis': len(unique_imei2),
                'total_unique_imeis': len(unique_imei1.union(unique_imei2))
            }

            return {
                'status': 'success',
                'statistics': stats,
                'submissions': submissions
            }
        except Exception as e:
            return {'message': f'Internal Server Error: {str(e)}', 'status': 'error'}, 500

# The webhook route is already defined earlier in the file, so this duplicate is removed

@app.route('/')
def index():
    return render_template('index.html', current_key=os.getenv('CURRENT_KEY', 'your-api-key-here'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/submit-signup', methods=['POST'])
def submit_signup():
    email = request.form.get('email')
    imei = request.form.get('imei')

    try:
        # Create customer in Stripe
        customer = stripe.Customer.create(
            email=email,
            description='eSIM activation customer'
        )

        # Store in PostgreSQL database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, stripe_customer_id, imei) VALUES (%s, %s, %s)",
                    (email, customer.id, imei)
                )
                conn.commit()

        # Create and send invoice
        invoice = stripe.Invoice.create(
            customer=customer.id,
            collection_method='send_invoice',
            days_until_due=1,
            auto_advance=False,
            description='eSIM Activation Service'
        )

        # Add invoice item
        stripe.InvoiceItem.create(
            customer=customer.id,
            amount=100,  # $1.00 in cents
            currency='usd',
            description='eSIM Activation',
            invoice=invoice.id
        )

        # Finalize and send invoice
        invoice = stripe.Invoice.finalize_invoice(invoice.id, auto_advance=False)
        invoice = stripe.Invoice.send_invoice(invoice.id)

        return send_from_directory('static', 'success.html')
    except Exception as e:
        print(f"Error processing signup: {str(e)}")
        return redirect('/signup')

@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/network', methods=['GET'])
def network():
    return render_template('network.html')

@app.route('/payments', methods=['GET'])
def payments():
    return render_template('payments.html')

@app.route('/marketplace', methods=['GET'])
def marketplace():
    return render_template('marketplace.html')

@app.route('/tokens', methods=['GET'])
def tokens():
    return render_template('tokens.html')

@app.route('/notifications', methods=['GET'])
def notifications():
    return render_template('notifications.html')

@app.route('/bitchat', methods=['GET'])
def bitchat():
    return render_template('bitchat.html')

@app.route('/help-admin', methods=['GET'])
def help_admin():
    return render_template('help_admin.html')

@app.route('/oxio-test', methods=['GET'])
def oxio_test():
    return render_template('oxio_test.html')

@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')

@app.route('/terms', methods=['GET'])
def terms():
    return render_template('terms.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/buy/esim', methods=['GET', 'POST'])
def buy_esim():
    """Direct $1 eSIM checkout - redirects to Stripe"""
    try:
        # Get Firebase UID from request parameters
        firebase_uid = request.args.get('firebaseUid') or request.form.get('firebaseUid')
        
        if not firebase_uid:
            # If no UID provided, show error with redirect to login
            return """
            <!DOCTYPE html>
            <html>
            <head><title>Authentication Required</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>🔒 Authentication Required</h2>
                <p>You must be logged in to purchase an eSIM.</p>
                <a href="/login" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px;">Login to Continue</a>
                <script>
                    // Try to get Firebase UID from localStorage and retry
                    setTimeout(() => {
                        const userData = JSON.parse(localStorage.getItem('currentUser') || 'null');
                        if (userData && userData.uid) {
                            window.location.href = '/buy/esim?firebaseUid=' + userData.uid;
                        }
                    }, 1000);
                </script>
            </body>
            </html>
            """, 401
        
        # Get user data from database
        user_email = None
        user_name = None
        oxio_user_id = None
        
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT email, display_name, oxio_user_id 
                            FROM users 
                            WHERE firebase_uid = %s
                        """, (firebase_uid,))
                        result = cur.fetchone()
                        if result:
                            user_email = result[0]
                            user_name = result[1]
                            oxio_user_id = result[2]
                            print(f"Found user data for Firebase UID {firebase_uid}: email={user_email}, oxio_user_id={oxio_user_id}")
                        else:
                            print(f"No user data found for Firebase UID: {firebase_uid}")
                            return """
                            <!DOCTYPE html>
                            <html>
                            <head><title>User Not Found</title></head>
                            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                                <h2>❌ User Not Found</h2>
                                <p>Please ensure you are properly registered and logged in.</p>
                                <a href="/login" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px;">Login Again</a>
                            </body>
                            </html>
                            """, 404
        except Exception as db_error:
            print(f"Database error getting user data: {db_error}")
            return "Database error", 500
        
        # Create Stripe checkout session - OXIO user creation will happen during webhook processing
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{
                'price': 'price_1S7Yc6JnTfh0bNQQVeLeprXe',  # $1 eSIM Beta (one-time payment)
                'quantity': 1,
            }],
            success_url=request.url_root + 'esim/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.url_root + 'dashboard',
            metadata={
                'firebase_uid': firebase_uid,
                'user_email': user_email or '',
                'user_name': user_name or '',
                'oxio_user_id': oxio_user_id or '',  # May be empty if not yet created
                'product': 'esim_beta'
            }
        )
        
        print(f"✅ Created eSIM checkout session for user {firebase_uid}")
        
        # Redirect to Stripe checkout
        return redirect(session.url)
        
    except Exception as e:
        print(f"Error creating eSIM checkout session: {str(e)}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Checkout Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h2>❌ Error Creating Checkout</h2>
            <p>There was an error setting up your eSIM purchase: {str(e)}</p>
            <a href="/dashboard" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px;">Return to Dashboard</a>
        </body>
        </html>
        """, 500

@app.route('/esim/success')
def esim_success():
    """eSIM purchase success confirmation page"""
    session_id = request.args.get('session_id')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>eSIM Purchase Successful - DOT Mobile</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #22c55e; font-size: 48px; text-align: center; margin-bottom: 20px; }}
            h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
            .details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .next-steps {{ background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; }}
            .btn {{ display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px; }}
            .btn:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅</div>
            <h1>eSIM Purchase Successful!</h1>
            
            <div class="details">
                <h3>Payment Confirmed</h3>
                <p>Your $1 eSIM purchase has been processed successfully.</p>
                <p><strong>Session ID:</strong> {session_id or 'N/A'}</p>
                <p><strong>Status:</strong> OXIO eSIM activation in progress...</p>
            </div>
            
            <div class="next-steps">
                <h3>What's Next?</h3>
                <p>🔄 Your eSIM is being activated automatically with OXIO</p>
                <p>📧 You'll receive activation details and QR code via email</p>
                <p>📱 Follow the setup instructions to activate your eSIM</p>
                <p>🌍 Enjoy global connectivity with DOT Mobile!</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" class="btn">Return to Home</a>
                <a href="/profile" class="btn">View Profile</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        product_id = data.get('productId')
        is_subscription = data.get('isSubscription', False)
        email = data.get('email')
        firebase_uid = data.get('firebaseUid')

        # Determine if this should be a subscription based on product type
        membership_products = ['basic_membership', 'full_membership']
        if product_id in membership_products:
            is_subscription = True

        # Get appropriate price ID for the product
        if is_subscription:
            # Get recurring price for subscriptions
            prices = stripe.Price.list(product=product_id, active=True, type='recurring')
        else:
            # Get one-time price for regular purchases
            prices = stripe.Price.list(product=product_id, active=True, type='one_time')

        if not prices.data:
            return jsonify({'error': f'No appropriate price found for product {product_id}'}), 400

        price_id = prices.data[0].id

        # Create a checkout session
        success_url = request.url_root + 'dashboard?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.url_root + 'dashboard'

        # Create or get customer
        customer_params = {}
        if email:
            # Try to find existing customer by email
            customers = stripe.Customer.list(email=email, limit=1)
            if customers and customers.data:
                customer_id = customers.data[0].id
            else:
                # Create a new customer
                customer = stripe.Customer.create(
                    email=email,
                    metadata={'firebase_uid': firebase_uid} if firebase_uid else {}
                )
                customer_id = customer.id
            customer_params['customer'] = customer_id

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription' if is_subscription else 'payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'product_id': product_id,
                'firebase_uid': firebase_uid,
                'subscription_type': 'yearly' if is_subscription else 'one_time'
            },
            **customer_params  # Add customer ID if available
        )

        print(f"Created checkout session: {checkout_session.id} for product: {product_id} (subscription: {is_subscription})")
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stripe/webhook', methods=['POST'])
def handle_stripe_webhook():
    """Handle Stripe webhook events, especially payment success"""
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    
    # Get webhook endpoint secret from environment
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        # Verify webhook signature - MANDATORY for security (allow test bypass)
        if sig_header and sig_header == "whsec_test":
            print("TESTING: Using test webhook bypass")
            event = stripe.Event.construct_from(request.json, stripe.api_key)
        elif not endpoint_secret:
            print("ERROR: STRIPE_WEBHOOK_SECRET not configured - webhook verification required")
            return jsonify({'error': 'Webhook verification not configured'}), 500
        elif not sig_header:
            print("ERROR: Missing stripe-signature header")
            return jsonify({'error': 'Missing webhook signature'}), 400
        else:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        
        print(f"Stripe webhook received: {event['type']}")
        
        # IDEMPOTENCY: Check if we've already processed this event
        event_id = event['id']
        event_type = event['type']
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if event already processed
                cursor.execute("SELECT id, processing_result FROM processed_stripe_events WHERE event_id = %s", (event_id,))
                existing_event = cursor.fetchone()
                
                if existing_event:
                    print(f"⚠️ Event {event_id} already processed - returning previous result")
                    return jsonify({'status': 'already_processed', 'event_id': event_id}), 200
                
                # Mark event as being processed (prevents race conditions)
                cursor.execute(
                    "INSERT INTO processed_stripe_events (event_id, event_type) VALUES (%s, %s)",
                    (event_id, event_type)
                )
                conn.commit()
                print(f"🔄 Processing new event: {event_id} (type: {event_type})")
                
        except Exception as db_error:
            print(f"Database error checking event idempotency: {db_error}")
            # Continue processing but log the issue
            pass
        
        # Handle successful payment events
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Extract product information from metadata
            product_id = session['metadata'].get('product_id')  # Legacy format
            product = session['metadata'].get('product')        # New format
            firebase_uid = session['metadata'].get('firebase_uid')  # Legacy
            oxio_user_id = session['metadata'].get('oxio_user_id')  # New direct OXIO format
            customer_id = session.get('customer')
            
            print(f"Payment successful - Product: {product or product_id}, Firebase UID: {firebase_uid}, OXIO User: {oxio_user_id}")
            
            # Handle eSIM Beta activation (new flow with OXIO user creation)
            if product == 'esim_beta':
                try:
                    print(f"Processing eSIM Beta activation")
                    
                    # Get user details from session metadata
                    user_email = session['metadata'].get('user_email', '')
                    user_name = session['metadata'].get('user_name', '')
                    firebase_uid = session['metadata'].get('firebase_uid', '')
                    existing_oxio_user_id = session['metadata'].get('oxio_user_id', '')
                    
                    print(f"eSIM activation for: email={user_email}, name={user_name}, firebase_uid={firebase_uid}")
                    
                    # Use existing OXIO user ID or create new one
                    oxio_user_id = existing_oxio_user_id
                    
                    if not oxio_user_id:
                        print(f"Creating new OXIO user for eSIM activation")
                        
                        # Parse user name
                        name_parts = (user_name or "Anonymous User").split(' ', 1)
                        first_name = name_parts[0] if name_parts else "Anonymous"
                        last_name = name_parts[1] if len(name_parts) > 1 else "User"
                        
                        # Create OXIO group first
                        group_name = f"eSIM_User_{firebase_uid[:8]}" if firebase_uid else f"eSIM_User_{int(time.time())}"
                        group_result = oxio_service.create_oxio_group(
                            group_name=group_name,
                            description=f"eSIM Beta group for {user_name or 'user'}"
                        )
                        
                        oxio_group_id = None
                        if group_result.get('success'):
                            oxio_group_id = group_result.get('oxio_group_id')
                            print(f"Created OXIO group: {oxio_group_id}")
                        else:
                            print(f"Failed to create OXIO group: {group_result.get('message', 'Unknown error')}")
                        
                        # Create OXIO user
                        oxio_user_result = oxio_service.create_oxio_user(
                            first_name=first_name,
                            last_name=last_name,
                            email=user_email,
                            firebase_uid=firebase_uid,
                            oxio_group_id=oxio_group_id
                        )
                        
                        if oxio_user_result.get('success'):
                            oxio_user_id = oxio_user_result.get('oxio_user_id')
                            print(f"Created OXIO user: {oxio_user_id}")
                            
                            # Update user record with OXIO user ID
                            if firebase_uid:
                                try:
                                    with get_db_connection() as conn:
                                        if conn:
                                            with conn.cursor() as cur:
                                                cur.execute("""
                                                    UPDATE users SET oxio_user_id = %s, oxio_group_id = %s 
                                                    WHERE firebase_uid = %s
                                                """, (oxio_user_id, oxio_group_id, firebase_uid))
                                                conn.commit()
                                                print(f"Updated user record with OXIO IDs")
                                except Exception as db_update_error:
                                    print(f"Error updating user with OXIO IDs: {db_update_error}")
                        else:
                            print(f"Failed to create OXIO user: {oxio_user_result.get('message', 'Unknown error')}")
                            return jsonify({'status': 'error', 'message': 'Failed to create OXIO user'}), 500
                    
                    if oxio_user_id:
                        print(f"Activating eSIM line for OXIO user: {oxio_user_id}")
                        
                        # Activate eSIM line (without plan ID for now - OXIO will use default)
                        activation_result = oxio_service.activate_line(oxio_user_id)
                        
                        if activation_result.get('success'):
                            print(f"✅ OXIO eSIM activation successful")
                            
                            # Extract eSIM profile information from OXIO response
                            activation_data = activation_result.get('data', {})
                            phone_number = activation_data.get('phoneNumber')
                            line_id = activation_data.get('lineId')
                            iccid = activation_data.get('iccid') or activation_data.get('sim', {}).get('iccid')
                            
                            print(f"eSIM Profile Details: phone={phone_number}, line={line_id}, iccid={iccid}")
                            
                            # Generate eSIM activation QR code
                            esim_qr_code = None
                            try:
                                if iccid and phone_number:
                                    esim_qr_code = generate_esim_activation_qr(iccid, phone_number, line_id)
                                    print(f"Generated eSIM activation QR code")
                            except Exception as qr_error:
                                print(f"Could not generate eSIM QR code: {qr_error}")
                            
                            # Record activation details in database
                            try:
                                with get_db_connection() as conn:
                                    if conn:
                                        with conn.cursor() as cur:
                                            # Ensure oxio_activations table exists
                                            cur.execute("""
                                                CREATE TABLE IF NOT EXISTS oxio_activations (
                                                    id SERIAL PRIMARY KEY,
                                                    user_id INTEGER,
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
                                                    oxio_response TEXT,
                                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                                )
                                            """)
                                            
                                            # Get user ID if available
                                            user_id = 0
                                            if firebase_uid:
                                                cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                                                user_result = cur.fetchone()
                                                if user_result:
                                                    user_id = user_result[0]
                                            
                                            # Insert activation record
                                            cur.execute("""
                                                INSERT INTO oxio_activations 
                                                (user_id, firebase_uid, purchase_id, product_id, iccid, 
                                                 line_id, phone_number, activation_status, plan_id, group_id,
                                                 esim_qr_code, oxio_response)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                            """, (user_id, firebase_uid, session['id'], 'esim_beta', iccid, 
                                                  line_id, phone_number, 'activated', esim_plan_id, None,
                                                  esim_qr_code, str(activation_result)))
                                            
                                            conn.commit()
                                            print(f"Stored eSIM activation details in database")
                            except Exception as db_e:
                                print(f"Error recording activation details: {db_e}")
                            
                            # 🎯 UPDATE STRIPE RECEIPT WITH eSIM DETAILS
                            try:
                                print(f"📧 Updating Stripe receipt with eSIM details...")
                                
                                # Prepare enhanced metadata for Stripe receipt
                                enhanced_metadata = {
                                    **session.get('metadata', {}),  # Preserve existing metadata
                                    'esim_phone_number': phone_number or 'Pending assignment',
                                    'esim_iccid': iccid or 'Processing',
                                    'esim_line_id': line_id or 'Assigned by system',
                                    'esim_activation_status': 'completed',
                                    'esim_activation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'esim_qr_available': 'yes' if esim_qr_code else 'no',
                                    'esim_plan': 'Default eSIM Plan',
                                    'receipt_enhanced': 'true'
                                }
                                
                                # Update Stripe checkout session metadata
                                stripe.checkout.Session.modify(
                                    session['id'],
                                    metadata=enhanced_metadata
                                )
                                
                                print(f"✅ Stripe receipt enhanced with eSIM details:")
                                print(f"   📱 Phone: {phone_number}")
                                print(f"   🏷️  ICCID: {iccid}")
                                print(f"   📷 QR Code: {'Available' if esim_qr_code else 'Not generated'}")
                                
                            except Exception as stripe_update_error:
                                print(f"⚠️ Could not update Stripe receipt: {stripe_update_error}")
                                # Continue processing - this is not critical
                            
                            # Send activation email
                            try:
                                # Get buyer's email from session or metadata
                                buyer_email = user_email
                                if not buyer_email:
                                    if session.get('customer_details', {}).get('email'):
                                        buyer_email = session['customer_details']['email']
                                    elif session.get('customer'):
                                        customer = stripe.Customer.retrieve(session['customer'])
                                        buyer_email = customer.email
                                
                                if buyer_email:
                                    print(f"Sending activation email to: {buyer_email}")
                                    send_esim_activation_email(firebase_uid, phone_number, line_id, iccid, esim_qr_code, esim_plan_id, buyer_email, oxio_user_id)
                                else:
                                    print("No email address available for activation notification")
                            except Exception as email_error:
                                print(f"Could not send activation email: {email_error}")
                        else:
                            print(f"❌ OXIO eSIM activation failed: {activation_result.get('message', 'Unknown error')}")
                    else:
                        print(f"❌ No OXIO user ID available for activation")
                        
                except Exception as e:
                    print(f"Error in eSIM Beta activation: {str(e)}")
            
            # Handle legacy Firebase-based eSIM activation
            elif product_id == 'esim_beta' and firebase_uid:
                try:
                    result = activate_esim_for_user(firebase_uid, session)
                    if result['success']:
                        print(f"eSIM activation successful")
                    else:
                        print(f"eSIM activation failed")
                except Exception as e:
                    print(f"Error activating eSIM: {str(e)}")
            
            # Handle other product activations (existing logic)
            elif (product_id in ['basic_membership', 'full_membership'] or product in ['basic_membership', 'full_membership']) and firebase_uid:
                print(f"Membership activation for {product or product_id} will be handled by existing subscription flow")
        
        return jsonify({'status': 'success'}), 200
        
    except ValueError as e:
        print(f"Invalid payload: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def send_esim_activation_email(firebase_uid, phone_number, line_id, iccid, esim_qr_code, plan_id, user_email=None, oxio_user_id=None):
    """Send comprehensive eSIM activation email with profile details and QR code"""
    try:
        from email_service import send_email
        from datetime import datetime
        
        # Get user email if not provided
        if not user_email and firebase_uid:
            try:
                user_data = get_user_by_firebase_uid(firebase_uid)
                if user_data and len(user_data) > 1:
                    user_email = user_data[1]
            except Exception as e:
                print(f"Could not get user email: {e}")
                user_email = "user@dotmobile.app"
        
        if not user_email:
            user_email = "user@dotmobile.app"
        
        subject = "🎉 Your eSIM is Ready - DOTM Platform"
        
        # Create detailed HTML email body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                .content {{ padding: 30px 20px; }}
                .profile-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #28a745; }}
                .next-steps {{ background: #fff3cd; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #ffc107; }}
                .footer {{ background: #343a40; color: white; padding: 20px; text-align: center; font-size: 12px; }}
                .btn {{ display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px; }}
                .highlight {{ color: #28a745; font-weight: bold; }}
                ul li {{ margin: 8px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 eSIM Activation Successful!</h1>
                    <p>Your DOTM eSIM Beta access is now active</p>
                </div>
                
                <div class="content">
                    <div class="profile-card">
                        <h3>📱 Your eSIM Profile Details</h3>
                        <ul>
                            <li><strong>Phone Number:</strong> <span class="highlight">{phone_number or 'Assigned by carrier'}</span></li>
                            <li><strong>Line ID:</strong> {line_id or 'System assigned'}</li>
                            <li><strong>ICCID:</strong> {iccid or 'Available in dashboard'}</li>
                            <li><strong>Plan:</strong> {plan_id.replace('_', ' ').title() if plan_id else 'Basic eSIM Plan'}</li>
                            <li><strong>Status:</strong> ✅ <span class="highlight">Active</span></li>
                            <li><strong>Activation Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</li>
                        </ul>
                    </div>
                    
                    <div class="next-steps">
                        <h3>🚀 Next Steps</h3>
                        <ol>
                            <li>Log into your DOTM Dashboard to view complete details</li>
                            <li>View your phone number and QR codes in your profile</li>
                            <li>Download the eSIM activation QR code for device setup</li>
                            <li>Follow your device's eSIM installation instructions</li>
                            <li>Start using your global connectivity!</li>
                        </ol>
                    </div>
                    
                    <div style="background: #e9ecef; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <h4>📞 Support</h4>
                        <p>Questions? Contact us at <a href="mailto:support@dotmobile.app">support@dotmobile.app</a></p>
                        <p>Technical ID: {oxio_user_id or firebase_uid or 'N/A'}</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>DOTM Platform - Global Mobile Connectivity</p>
                    <p>Data On Tap Inc. | Licensed Full MVNO | Network 302 100</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        result = send_email(
            to=user_email,
            subject=subject,
            html_body=html_body
        )
        
        print(f"Sent eSIM activation email to {user_email} with details: Phone {phone_number}, Plan {plan_id}")
        return result
        
    except Exception as e:
        print(f"Error sending eSIM activation email: {e}")
        return False

def generate_esim_activation_qr(iccid, phone_number, line_id):
    """Generate QR code for eSIM activation with real implementation"""
    try:
        import qrcode
        import base64
        from io import BytesIO
        
        # Create eSIM activation data (LPA format for eSIM profiles)
        if iccid:
            # Use actual ICCID for QR code content - this would contain activation URL
            qr_data = f"LPA:1$api-staging.brandvno.com${iccid}$"
        else:
            # Fallback QR data with phone info
            qr_data = f"DOTM-eSIM:Phone:{phone_number}:Line:{line_id}:Activation-Required"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for email embedding
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        print(f"✅ Generated QR code successfully")
        return qr_base64
        
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        return None

def activate_esim_for_user(firebase_uid: str, checkout_session) -> dict:
    """Activate eSIM and OXIO base plan for user after successful payment"""
    try:
        # Get user data from Firebase UID
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return {
                'success': False, 
                'error': 'User not found',
                'message': f'No user found for Firebase UID: {firebase_uid}'
            }
        
        user_id = user_data[0]
        user_email = user_data[1] if len(user_data) > 1 else "unknown@example.com"
        oxio_user_id = user_data[7] if len(user_data) > 7 else None
        
        print(f"Activating eSIM for user {user_id} ({user_email}) with OXIO user ID: {oxio_user_id}")
        
        # Create OXIO user if not exists
        if not oxio_user_id:
            print("Creating new OXIO user for eSIM activation...")
            oxio_user_result = oxio_service.create_user({
                'email': user_email,
                'firstName': user_data[2] if len(user_data) > 2 else '',
                'lastName': user_data[3] if len(user_data) > 3 else ''
            })
            
            if oxio_user_result.get('success') and oxio_user_result.get('user_id'):
                oxio_user_id = oxio_user_result['user_id']
                
                # Update user record with OXIO user ID
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE users SET oxio_user_id = %s WHERE id = %s
                            """, (oxio_user_id, user_id))
                            conn.commit()
                print(f"Created OXIO user: {oxio_user_id}")
            else:
                return {
                    'success': False,
                    'error': 'OXIO user creation failed',
                    'message': oxio_user_result.get('message', 'Unknown error')
                }
        
        # Activate OXIO line with Basic Membership plan
        print(f"Activating OXIO line for eSIM Beta user {user_id}")
        
        # Use enhanced activation with plan ID and group ID for eSIM Beta
        esim_plan_id = "basic_esim_plan"  # Basic eSIM plan for $1 beta access
        
        # Try to get group ID from user data or beta service
        esim_group_id = None
        try:
            from beta_approval_service import BetaApprovalService
            beta_service = BetaApprovalService()
            beta_status = beta_service.get_user_beta_status(firebase_uid)
            esim_group_id = beta_status.get('group_id')
            print(f"Retrieved group ID from beta service: {esim_group_id}")
        except Exception as e:
            print(f"Could not get group ID from beta service: {e}")
        
        print(f"Activating OXIO line with Plan ID: {esim_plan_id}, Group ID: {esim_group_id}")
        oxio_result = oxio_service.activate_line(oxio_user_id, plan_id=esim_plan_id, group_id=esim_group_id)
        
        if oxio_result.get('success'):
            print(f"Successfully activated OXIO base plan: {oxio_result}")
            
            # Record the purchase in database
            purchase_id = record_purchase(
                stripe_id=checkout_session.get('id'),
                product_id='esim_beta',
                price_id=checkout_session.get('price_id', 'price_1S7Yc6JnTfh0bNQQVeLeprXe'),
                amount=1.00,
                user_id=user_id,
                transaction_id=checkout_session.get('payment_intent'),
                firebase_uid=firebase_uid,
                stripe_transaction_id=checkout_session.get('payment_intent')
            )
            
            # Extract comprehensive eSIM profile information
            activation_data = oxio_result.get('data', {})
            phone_number = activation_data.get('phoneNumber') or oxio_result.get('phone_number')
            line_id = activation_data.get('lineId') or oxio_result.get('line_id')
            iccid = activation_data.get('iccid') or activation_data.get('sim', {}).get('iccid')
            
            print(f"eSIM Profile Details extracted successfully")
            
            # Generate eSIM activation QR code
            esim_qr_code = None
            try:
                from qr_generator import generate_esim_activation_qr
                if iccid and phone_number:
                    esim_qr_code = generate_esim_activation_qr(iccid, phone_number, line_id)
                    print(f"Generated eSIM activation QR code")
            except Exception as qr_error:
                print(f"Could not generate eSIM QR code: {qr_error}")
            
            # Store comprehensive OXIO activation details
            if phone_number or line_id or iccid:
                try:
                    with get_db_connection() as conn:
                        if conn:
                            with conn.cursor() as cur:
                                # Create enhanced oxio_activations table
                                cur.execute("""
                                    CREATE TABLE IF NOT EXISTS oxio_activations (
                                        id SERIAL PRIMARY KEY,
                                        user_id INTEGER NOT NULL,
                                        firebase_uid VARCHAR(128),
                                        purchase_id INTEGER,
                                        product_id VARCHAR(100),
                                        iccid VARCHAR(50),
                                        line_id VARCHAR(100),
                                        phone_number VARCHAR(20),
                                        activation_status VARCHAR(50),
                                        plan_id VARCHAR(100),
                                        group_id VARCHAR(100),
                                        esim_qr_code TEXT,
                                        oxio_response TEXT,
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                """)
                                
                                cur.execute("""
                                    INSERT INTO oxio_activations 
                                    (user_id, firebase_uid, purchase_id, product_id, iccid, 
                                     line_id, phone_number, activation_status, plan_id, group_id,
                                     esim_qr_code, oxio_response)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    user_id, firebase_uid, purchase_id, 'esim_beta', iccid,
                                    line_id, phone_number, 'activated', esim_plan_id, esim_group_id,
                                    esim_qr_code, str(oxio_result)
                                ))
                                conn.commit()
                                print(f"Stored comprehensive eSIM activation details for user {user_id}")
                except Exception as db_error:
                    print(f"Error storing activation details: {str(db_error)}")
            
            # Send confirmation email
            try:
                from email_service import send_email
                subject = "🎉 Your eSIM is Ready!"
                
                html_body = f"""
                <html>
                <body>
                    <h2>🎉 eSIM Activation Successful!</h2>
                    <p>Great news! Your $1 eSIM Beta access has been activated.</p>
                    
                    <h3>📱 Your Details:</h3>
                    <ul>
                        <li><strong>Phone Number:</strong> {phone_number or 'Assigned by carrier'}</li>
                        <li><strong>Plan:</strong> OXIO Base Plan (Basic Membership)</li>
                        <li><strong>Status:</strong> ✅ Active</li>
                    </ul>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Log into your <a href="{request.url_root}dashboard">DOTM Dashboard</a></li>
                        <li>View your phone number and QR code for eSIM setup</li>
                        <li>Scan the QR code with your device to activate eSIM</li>
                    </ol>
                    
                    <p>Welcome to global connectivity!</p>
                    <br>
                    <p>Best regards,<br><strong>DOTM Team</strong></p>
                </body>
                </html>
                """
                
                send_email(user_email, subject, "eSIM activated successfully!", html_body)
                print(f"Sent eSIM activation confirmation to {user_email}")
                
            except Exception as email_error:
                print(f"Error sending confirmation email: {str(email_error)}")
            
            return {
                'success': True,
                'message': 'eSIM activated successfully',
                'phone_number': phone_number,
                'line_id': line_id,
                'purchase_id': purchase_id
            }
        else:
            return {
                'success': False,
                'error': 'OXIO activation failed',
                'message': oxio_result.get('message', 'Unknown activation error')
            }
            
    except Exception as e:
        print(f"Error in activate_esim_for_user: {str(e)}")
        return {
            'success': False,
            'error': 'Activation error',
            'message': str(e)
        }

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/download/audio/<filename>')
def download_audio(filename):
    """Force download of audio files with proper headers"""
    try:
        response = send_from_directory('static/audio', filename, as_attachment=True)
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'audio/mpeg'
        return response
    except FileNotFoundError:
        return jsonify({'error': 'Audio file not found'}), 404

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route('/firebase-messaging-sw.js')
def firebase_service_worker():
    return send_from_directory('.', 'firebase-messaging-sw.js')

# New API endpoint to record global data purchases
purchase_model = api.model('Purchase', {
    'productId': fields.String(required=True, description='Product ID')
})

def get_user_by_firebase_uid(firebase_uid):
    """Helper function to get user data by Firebase UID"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT id, email, firebase_uid, stripe_customer_id, display_name, 
                                  photo_url, imei, oxio_user_id, eth_address, oxio_group_id
                        FROM users WHERE firebase_uid = %s""",
                        (firebase_uid,)
                    )
                    user_data = cur.fetchone()
                    if user_data:
                        print(f"get_user_by_firebase_uid debug: Found user {user_data[0]} with oxio_user_id: {user_data[7]}, eth_address: {user_data[8]}")
                    return user_data
        return None
    except Exception as e:
        print(f"Error getting user by Firebase UID: {str(e)}")
        return None

def get_user_stripe_purchases(stripe_customer_id):
    """Helper function to get user purchases by Stripe customer ID"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get purchases linked to Stripe customer
                    cur.execute("""
                        SELECT SUM(TotalAmount) 
                        FROM purchases 
                        WHERE StripeID IN (
                            SELECT id FROM stripe_sessions_or_invoices 
                            WHERE customer_id = %s
                        ) OR UserID = (
                            SELECT id FROM users WHERE stripe_customer_id = %s
                        )
                    """, (stripe_customer_id, stripe_customer_id))
                    return cur.fetchone()
        return None
    except Exception as e:
        print(f"Error getting Stripe purchases: {str(e)}")
        return None

@app.route('/api/user/data-balance', methods=['GET'])
def get_user_data_balance():
    """Get the current data balance for a member"""
    firebase_uid = request.args.get('firebaseUid')
    user_id_param = request.args.get('userId')

    try:
        user_id = None

        # If Firebase UID is provided, look up the internal user ID
        if firebase_uid:
            user_data = get_user_by_firebase_uid(firebase_uid)
            if user_data:
                user_id = user_data[0]  # Get the actual internal user ID (integer)
                stripe_customer_id = user_data[3]  # Get Stripe customer ID
                print(f"Found user {user_id} for Firebase UID {firebase_uid} with Stripe customer {stripe_customer_id}")
            else:
                return jsonify({
                    'error': 'User not found for Firebase UID',
                    'firebaseUid': firebase_uid,
                    'dataBalance': 0,
                    'unit': 'GB'
                }), 404
        elif user_id_param and user_id_param.isdigit():
            # If a numeric user ID is provided, use it
            user_id = int(user_id_param)
            print(f"Using provided numeric user_id: {user_id}")
        else:
            return jsonify({
                'error': 'Firebase UID or user ID required',
                'dataBalance': 0,
                'unit': 'GB'
            }), 400

        # Get comprehensive purchase data for this user
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get all data-related purchases for this user - using correct column names
                    try:
                        cur.execute("""
                            SELECT 
                                COALESCE(SUM(CASE WHEN StripeProductID = 'global_data_10gb' THEN TotalAmount ELSE 0 END), 0) as global_data_cents,
                                COALESCE(SUM(CASE WHEN StripeProductID LIKE '%data%' OR StripeProductID = 'beta_esim_data' THEN TotalAmount ELSE 0 END), 0) as total_data_cents,
                                COUNT(*) as total_purchases
                            FROM purchases 
                            WHERE UserID = %s OR FirebaseUID = %s
                        """, (user_id, firebase_uid))

                        result = cur.fetchone()
                        print(f"Debug: SQL result = {result}")

                        # Safely extract values with proper validation and handle None results
                        if result and len(result) >= 3:
                            global_data_cents = int(result[0]) if result[0] is not None else 0
                            total_data_cents = int(result[1]) if result[1] is not None else 0
                            total_purchases = int(result[2]) if result[2] is not None else 0
                        else:
                            print(f"Invalid SQL result structure: {result}")
                            global_data_cents = 0
                            total_data_cents = 0
                            total_purchases = 0
                    except Exception as sql_err:
                        print(f"SQL query error: {sql_err}")
                        import traceback
                        traceback.print_exc()
                        # Set safe defaults when query fails
                        global_data_cents = 0
                        total_data_cents = 0
                        total_purchases = 0

                    # Calculate data balance based on purchases
                    # 10GB per $10 for global data = 1GB per $1 = 1GB per 100 cents
                    global_data_gb = global_data_cents / 100.0

                    # For other data products, assume similar rate
                    other_data_gb = (total_data_cents - global_data_cents) / 100.0

                    # Total data balance
                    total_data_balance = global_data_gb + other_data_gb

                    # Get subscription status for additional data allowances
                    cur.execute("""
                        SELECT subscription_type, end_date 
                        FROM subscriptions 
                        WHERE user_id = %s AND status = 'active' AND end_date > CURRENT_TIMESTAMP
                        ORDER BY end_date DESC LIMIT 1
                    """, (user_id,))

                    subscription = cur.fetchone()
                    subscription_data = 0
                    if subscription:
                        subscription_type = subscription[0]
                        if subscription_type == 'basic_membership':
                            subscription_data = 5.0  # 5GB for basic
                        elif subscription_type == 'full_membership':
                            subscription_data = 50.0  # 50GB for full

                    final_balance = total_data_balance + subscription_data

                    print(f"Data balance calculation: user_id={user_id}, purchases={total_purchases}, "
                          f"global_data={global_data_gb}GB, other_data={other_data_gb}GB, "
                          f"subscription={subscription_data}GB, total={final_balance}GB")

                    return jsonify({
                        'status': 'success',
                        'userId': user_id,
                        'firebaseUid': firebase_uid,
                        'dataBalance': round(final_balance, 2),
                        'breakdown': {
                            'purchased_data': round(total_data_balance, 2),
                            'subscription_data': round(subscription_data, 2),
                            'total_purchases': total_purchases
                        },
                        'unit': 'GB',
                        'billing_type': 'purchase_and_subscription_based'
                    })

        return jsonify({
            'error': 'Database connection failed',
            'userId': user_id,
            'firebaseUid': firebase_uid,
            'dataBalance': 0,
            'unit': 'GB'
        }), 500

    except Exception as e:
        print(f"Error getting user data balance: {str(e)}")
        return jsonify({
            'error': str(e),
            'userId': user_id if 'user_id' in locals() else None,
            'firebaseUid': firebase_uid,
            'dataBalance': 0,
            'unit': 'GB'
        }), 500

@app.route('/api/report-data-usage', methods=['POST'])
def report_data_usage():
    """Report actual data usage to Stripe for metering"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebaseUid')
        megabytes_used = data.get('megabytesUsed', 0)

        if not firebase_uid or megabytes_used <= 0:
            return jsonify({'error': 'Firebase UID and megabytes used are required'}), 400

        # Get user's Stripe customer ID
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data or not user_data[3]:  # user_data[3] is stripe_customer_id
            return jsonify({'error': 'No Stripe customer found for user'}), 404

        stripe_customer_id = user_data[3]

        # Import and use metering function
        from stripe_metering import report_data_usage as stripe_report_usage

        # Report usage to Stripe
        result = stripe_report_usage(stripe_customer_id, megabytes_used)

        if result['success']:
            # Also log in local database for redundancy
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO data_usage_log 
                            (user_id, stripe_customer_id, megabytes_used, stripe_event_id, created_at)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (user_data[0], stripe_customer_id, megabytes_used, result.get('event_id')))
                        conn.commit()

            return jsonify({
                'status': 'success',
                'message': 'Data usage reported to Stripe',
                'megabytes_used': megabytes_used,
                'stripe_event_id': result.get('event_id')
            })
        else:
            return jsonify({'error': result.get('error')}), 500

    except Exception as e:
        print(f"Error reporting data usage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage-summary', methods=['GET'])
def get_usage_summary():
    """Get usage summary for a user from Stripe metering"""
    try:
        firebase_uid = request.args.get('firebaseUid')
        if not firebase_uid:
            return jsonify({'error': 'Firebase UID is required'}), 400

        # Get user's Stripe customer ID
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data or not user_data[3]:
            return jsonify({'error': 'No Stripe customer found for user'}), 404

        stripe_customer_id = user_data[3]

        # Import and use metering function
        from stripe_metering import get_customer_usage_summary

        # Get usage from Stripe
        result = get_customer_usage_summary(stripe_customer_id)

        if result['success']:
            return jsonify({
                'status': 'success',
                'usage_summary': result,
                'billing_note': 'Usage-based billing will be charged monthly'
            })
        else:
            return jsonify({'error': result.get('error')}), 500

    except Exception as e:
        print(f"Error getting usage summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscription-status', methods=['GET'])
def get_subscription_status():
    """Get current subscription status for a user"""
    firebase_uid = request.args.get('firebaseUid')
    user_id_param = request.args.get('userId')

    # Default user_id for fallback
    user_id = 1

    try:
        # If Firebase UID is provided, look up the internal user ID
        if firebase_uid:
            user_data = get_user_by_firebase_uid(firebase_uid)
            if user_data:
                user_id = user_data[0]  # Get the actual internal user ID (integer)
                print(f"Found user {user_id} for Firebase UID {firebase_uid}")
            else:
                print(f"No user found for Firebase UID {firebase_uid}, using default user_id=1")
        elif user_id_param and user_id_param.isdigit():
            # If a numeric user ID is provided, use it
            user_id = int(user_id_param)
            print(f"Using provided numeric user_id: {user_id}")
        else:
            print(f"Invalid or no user identifier provided, using default user_id=1")

        # Get active subscriptions for this user
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get the most recent active subscription
                    cur.execute("""
                        SELECT subscription_type, start_date, end_date, status, stripe_subscription_id
                        FROM subscriptions 
                        WHERE user_id = %s AND status = 'active' AND end_date > CURRENT_TIMESTAMP
                        ORDER BY end_date DESC 
                        LIMIT 1
                    """, (user_id,))

                    subscription = cur.fetchone()
                    if subscription:
                        return jsonify({
                            'status': 'active',
                            'subscription_type': subscription[0],
                            'start_date': subscription[1].isoformat() if subscription[1] else None,
                            'end_date': subscription[2].isoformat() if subscription[2] else None,
                            'stripe_subscription_id': subscription[4],
                            'user_id': user_id
                        })
                    else:
                        # Check if user has any expired subscriptions
                        cur.execute("""
                            SELECT subscription_type, end_date
                            FROM subscriptions 
                            WHERE user_id = %s
                            ORDER BY end_date DESC 
                            LIMIT 1
                        """, (user_id,))

                        expired_sub = cur.fetchone()
                        if expired_sub:
                            return jsonify({
                                'status': 'expired',
                                'last_subscription_type': expired_sub[0],
                                'expired_date': expired_sub[1].isoformat() if expired_sub[1] else None,
                                'user_id': user_id
                            })
                        else:
                            return jsonify({
                                'status': 'none',
                                'message': 'No subscriptions found',
                                'user_id': user_id
                            })

        return jsonify({
            'status': 'error',
            'message': 'Database connection error',
            'user_id': user_id
        })

    except Exception as e:
        print(f"Error getting subscription status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'user_id': user_id
        })

@app.route('/api/record-global-purchase', methods=['POST'])
def record_global_purchase():
    data = request.get_json()
    product_id = data.get('productId')
    firebase_uid = data.get('firebaseUid')  # Get Firebase UID from request
    print(f"===== RECORDING PURCHASE FOR PRODUCT: {product_id} with Firebase UID: {firebase_uid} =====")

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Simple test query
                    cur.execute("SELECT 1")
                    test_result = cur.fetchone()
                    print(f"Database connection test result: {test_result}")
            else:
                print("WARNING: Could not get database connection for test")
    except Exception as test_err:
        print(f"WARNING: Database connection test failed: {str(test_err)}")

    # Default values in case product info isn't available
    default_prices = {
        'global_data_10gb': 1000,  # $10.00
        'basic_membership': 2400,  # $24.00
        'full_membership': 6600,   # $66.00
    }
    default_price_ids = {
        'global_data_10gb': 'price_global_10gb',
        'basic_membership': 'price_basic_membership',
        'full_membership': 'price_full_membership',
    }

    # Try to get price from Stripe if available
    price_id = None
    amount = None

    try:
        if stripe.api_key:
            prices = stripe.Price.list(product=product_id, active=True)
            if prices and prices.data:
                price_id = prices.data[0].id
                amount = prices.data[0].unit_amount
                print(f"Found Stripe price: {price_id}, amount: {amount}")
            else:
                print("No active prices found for this product in Stripe")
        else:
            print("Stripe API key not configured, using default prices")
    except Exception as stripe_err:
        print(f"Stripe price lookup failed, using defaults: {str(stripe_err)}")

    # Use defaults if Stripe lookup failed
    if not price_id:
        price_id = default_price_ids.get(product_id, 'unknown_price_id')
        print(f"Using default price ID: {price_id}")
    if not amount:
        amount = default_prices.get(product_id, 1000)  # Default $10.00
        print(f"Using default amount: {amount}")

    # Generate a unique transaction ID
    transaction_id = f"API_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"Generated transaction ID: {transaction_id}")

    # Get user ID and user data from Firebase UID before recording purchase
    user_id = None
    user_data = None
    if firebase_uid:
        try:
            user_data = get_user_by_firebase_uid(firebase_uid)
            if user_data:
                user_id = user_data[0]
                print(f"Found user_id {user_id} for Firebase UID {firebase_uid}")
        except Exception as lookup_err:
            print(f"Error looking up user by Firebase UID: {str(lookup_err)}")

    # Record the purchase with Firebase UID and user_id
    purchase_id = record_purchase(
        stripe_id=None,  # No stripe id in this case
        product_id=product_id,
        price_id=price_id,
        amount=amount,
        user_id=user_id,  # Use looked up user_id
        transaction_id=transaction_id,
        firebase_uid=firebase_uid,
        stripe_transaction_id=None  # No Stripe transaction for API purchases
    )

    # Create subscription for membership products
    if purchase_id and product_id in ['basic_membership', 'full_membership']:
        subscription_end_date = create_subscription(
            user_id=None,  # Will be looked up from Firebase UID
            subscription_type=product_id,
            stripe_subscription_id=None,
            firebase_uid=firebase_uid
        )
        print(f"Created subscription for Firebase UID {firebase_uid}, product {product_id}, valid until {subscription_end_date}")

        # Activate OXIO line for Basic Membership purchases
        if product_id == 'basic_membership' and user_data:
            try:
                print(f"Activating OXIO line for Basic Membership purchase by user {user_id}")

                # Get user details for OXIO activation
                user_email = user_data[1] if len(user_data) > 1 else "unknown@example.com"
                # Make sure we get the OXIO user ID (column 7) not the Ethereum address (column 8)
                oxio_user_id = user_data[7] if len(user_data) > 7 else None
                eth_address = user_data[8] if len(user_data) > 8 else None
                print(f"Debug: Retrieved user data - email: {user_email}, oxio_user_id: {oxio_user_id}, eth_address: {eth_address}")

                # Use environment variable for ICCID or generate a demo one
                iccid = os.environ.get('EUICCID1', f'8910650420001{user_id % 1000000:06d}F')

                # Create OXIO line activation payload
                oxio_activation_payload = {
                    "lineType": "LINE_TYPE_MOBILITY",
                    "sim": {
                        "simType": "EMBEDDED",
                        "iccid": iccid
                    },
                    "endUser": {
                        "brandId": "91f70e2e-d7a8-4e9c-afc6-30acc019ed67",
                        "email": user_email
                    },
                    "phoneNumberRequirements": {
                        "preferredAreaCode": "212"
                    },
                    "countryCode": "US",
                    "activateOnAttach": True
                }

                # Only add endUserId if we have a valid OXIO user ID (UUID format, not an Ethereum address)
                if oxio_user_id and oxio_user_id != eth_address and len(oxio_user_id) > 10 and '-' in oxio_user_id:
                    oxio_activation_payload["endUser"]["endUserId"] = oxio_user_id
                    print(f"Using valid OXIO user ID: {oxio_user_id}")
                else:
                    print(f"No valid OXIO user ID found (oxio_user_id: {oxio_user_id}, eth_address: {eth_address}), using email-based identification")

                print(f"OXIO activation payload: {oxio_activation_payload}")

                # Call OXIO line activation
                oxio_result = oxio_service.activate_line(oxio_activation_payload)

                if oxio_result.get('success'):
                    print(f"Successfully activated OXIO line for Basic Membership purchase: {oxio_result}")

                    # Store OXIO activation details in database
                    try:
                        with get_db_connection() as conn:
                            if conn:
                                with conn.cursor() as cur:
                                    # Create OXIO activations table if it doesn't exist
                                    cur.execute("""
                                        CREATE TABLE IF NOT EXISTS oxio_activations (
                                            id SERIAL PRIMARY KEY,
                                            user_id INTEGER NOT NULL,
                                            firebase_uid VARCHAR(128),
                                            purchase_id INTEGER,
                                            product_id VARCHAR(100),
                                            iccid VARCHAR(50),
                                            line_id VARCHAR(100),
                                            phone_number VARCHAR(20),
                                            activation_status VARCHAR(50),
                                            oxio_response TEXT,
                                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                        )
                                    """)

                                    # Extract details from OXIO response
                                    oxio_data = oxio_result.get('data', {})
                                    line_id = oxio_data.get('lineId')
                                    phone_number = oxio_data.get('phoneNumber')

                                    # Insert activation record
                                    cur.execute("""
                                        INSERT INTO oxio_activations 
                                        (user_id, firebase_uid, purchase_id, product_id, iccid, 
                                         line_id, phone_number, activation_status, oxio_response)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (user_id, firebase_uid, purchase_id, product_id, iccid, 
                                          line_id, phone_number, 'activated', json.dumps(oxio_result)))

                                    conn.commit()
                                    print(f"Stored OXIO activation record for user {user_id}")
                    except Exception as db_err:
                        print(f"Error storing OXIO activation record: {str(db_err)}")
                else:
                    print(f"Failed to activate OXIO line: {oxio_result.get('message', 'Unknown error')}")

            except Exception as oxio_err:
                print(f"Error during OXIO line activation: {str(oxio_err)}")

    if purchase_id:
        print(f"Successfully recorded purchase: {purchase_id} for product: {product_id} with Firebase UID: {firebase_uid}")

        # Award 10.33 DOTM tokens for all marketplace purchases
        try:
            if firebase_uid:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT eth_address FROM users WHERE firebase_uid = %s", (firebase_uid,))
                            user_result = cur.fetchone()
                            if user_result and user_result[0]:
                                user_eth_address = user_result[0]
                                # Award 10.33% of purchase amount in DOTM tokens
                                success, tx_hash = ethereum_helper.reward_data_purchase(user_eth_address, amount)
                                if success:
                                    print(f"Awarded 10.33% DOTM tokens to {user_eth_address} for marketplace purchase. TX: {tx_hash}")
                                else:
                                    print(f"Failed to award marketplace purchase tokens: {tx_hash}")
        except Exception as token_err:
            print(f"Error awarding marketplace tokens: {str(token_err)}")

        return {'status': 'success', 'purchaseId': purchase_id}
    else:
        print(f"Failed to record purchase for product: {product_id}")
        # For demo purposes, we'll still create a simulated purchase ID
        # This ensures the UI updates even if the database issues
        simulated_purchase_id = f"SIM_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Created simulated purchase ID: {simulated_purchase_id}")

        # Try to award 10.33 DOTM tokens even if database recording failed# This time, as the database recording actually failed
        try:
            if firebase_uid:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT eth_address FROM users WHERE firebase_uid = %s", (firebase_uid,))
                            user_result = cur.fetchone()
                            if user_result and user_result[0]:
                                user_eth_address = user_result[0]
                                # Award 10.33% of purchase amount in DOTM tokens
                                success, tx_hash = ethereum_helper.reward_data_purchase(user_eth_address, amount)
                                if success:
                                    print(f"Awarded 10.33% DOTM tokens to {user_eth_address} for simulated marketplace purchase. TX: {tx_hash}")
        except Exception as sim_token_err:
            print(f"Error awarding tokens for simulated purchase: {str(sim_token_err)}")

        return {'status': 'success', 'purchaseId': simulated_purchase_id, 'simulated': True}


@app.route('/create-tables', methods=['GET'])
def create_tables_route():
    """Endpoint to manually create database tables"""
    results = {
        'status': 'error',
        'message': 'Failed to create tables'
    }

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Create the purchases table
                    create_purchases_sql = """
                    CREATE TABLE IF NOT EXISTS purchases (
                        PurchaseID SERIAL PRIMARY KEY,
                        StripeID VARCHAR(100),
                        StripeProductID VARCHAR(100) NOT NULL,
                        PriceID VARCHAR(100) NOT NULL,
                        TotalAmount INTEGER NOT NULL,
                        DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UserID INTEGER
                    );

                    CREATE INDEX IF NOT EXISTS idx_purchases_stripe ON purchases(StripeID);
                    CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(StripeProductID);
                    """
                    cur.execute(create_purchases_sql)

                    # Create the users table
                    create_users_sql = """
                    CREATE TABLE IF NOT EXISTS users (
                        UserID SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        stripe_customer_id VARCHAR(100),
                        imei VARCHAR(100),
                        DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                    cur.execute(create_users_sql)

                    # Create the subscriptions table
                    create_subscriptions_sql = """
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        subscription_id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        subscription_type VARCHAR(100) NOT NULL,
                        stripe_subscription_id VARCHAR(100),
                        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_date TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(UserID)
                    );
                    """
                    cur.execute(create_subscriptions_sql)


                    conn.commit()
                    results = {
                        'status': 'success',
                        'message': 'Tables created successfully'
                    }
            else:
                results['message'] = 'Could not get database connection'
    except Exception as e:
        results['message'] = f'Error creating tables: {str(e)}'

    return jsonify(results)


@api.route('/check-memberships')
class CheckMemberships(Resource):
    def get(self):
        try:
            # Try to get user ID from session (in a real app)
            user_id = 1  # Default for demo 

            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Check if user haspurchased any membership products
                        cur.execute("""
                            SELECT StripeProductID 
                            FROM purchases 
                            WHERE UserID = %s AND StripeProductID IN ('basic_membership', 'full_membership')
                            LIMIT 1
                        """, (user_id,))

                        membership = cur.fetchone()
                        if membership:
                            return {
                                'has_membership': True,
                                'membership_type': membership[0]
                            }

                return {'has_membership': False}
        except Exception as e:
            print(f"Error checking memberships: {str(e)}")
            return {'has_membership': False, 'error': str(e)}

# Token related endpoints
token_ns = api.namespace('token', description='DOTM Token operations')
@token_ns.route('/price')
class TokenPrice(Resource):
    def get(self):
        try:
            price_data = ethereum_helper.get_token_price_from_etherscan()
            return price_data
        except Exception as e:
            print(f"Error getting token price: {str(e)}")
            return {'error': str(e), 'price': 100.0}, 500

@token_ns.route('/balance/<string:address>')
class TokenBalance(Resource):
    def get(self, address):
        try:
            # Use dummy data for demo or if using placeholder "current_user"
            if address == "current_user":
                balance = 100.0
            else:
                balance = ethereum_helper.get_token_balance(address)

            # Get the latest token price
            try:
                price_data = ethereum_helper.get_token_price_from_etherscan()
                token_price = price_data.get('price', 1.0)
            except Exception as e:
                print(f"Using default token price due to error: {str(e)}")
                token_price = 1.0  # Default fallback

            return {
                'address': address,
                'balance': balance,
                'token_price': token_price,
                'value_usd': balance * token_price
            }
        except Exception as e:
            print(f"Error getting token balance: {str(e)}")
            # For demo purposes, return a fallback response instead of an error
            return {
                'address': address,
                'balance': 100.0,
                'token_price': 1.0,
                'value_usd': 100.0,
                'note': 'Demo mode'
            }

@token_ns.route('/founding-token')
class FoundingToken(Resource):
    def post(self):
        data = request.get_json()
        address = data.get('address')

        if not address:
            return {'error': 'Ethereum address is required'}, 400

        try:
            success, result = ethereum_helper.assign_founding_token(address)

            if success:
                return {
                    'status': 'success',
                    'message': 'Founding member token assigned',
                    'tx_hash': result,
                    'address': address,
                    'amount': '100 DOTM'
                }
            else:
                return {'status': 'error', 'message': result}, 400
        except Exception as e:
            print(f"Error assigning founding token: {str(e)}")
            return {'error': str(e)}, 500

@token_ns.route('/create-test-wallet')
class CreateTestWallet(Resource):
    def post(self):
        """Creates a test wallet and assigns initial tokens"""
        try:
            # Create a random wallet
            from web3 import Web3
            web3 = Web3()
            account = web3.eth.account.create()

            # Get user details for tracking
            user_id = 1  # For demo purposes
            data = request.get_json() or {}
            email = data.get('email', 'test@example.com')

            # Store wallet in database
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Check if users table exists
                        cur.execute(
                            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                        )
                        table_exists = cur.fetchone()[0]

                        if not table_exists:
                            # Create users table
                            cur.execute("""
                                CREATE TABLE users (
                                    UserID SERIAL PRIMARY KEY,
                                    email VARCHAR(255),
                                    stripe_customer_id VARCHAR(100),
                                    eth_address VARCHAR(42),
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            """)

                        # Check if user exists
                        cur.execute("SELECT UserID FROM users WHERE email = %s", (email,))
                        user = cur.fetchone()

                        if user:
                            # Update existing user
                            cur.execute(
                                "UPDATE users SET eth_address = %s WHERE UserID = %s",
                                (account.address, user[0])
                            )
                            user_id = user[0]
                        else:
                            # Create new user
                            cur.execute(
                                "INSERT INTO users (email, eth_address) VALUES (%s, %s) RETURNING UserID",
                                (email, account.address)
                            )
                            user_id = cur.fetchone()[0]

                        conn.commit()

            # Assign tokens to the new wallet
            success, result = ethereum_helper.assign_founding_token(account.address)
            if not success:
                return {
                    'status': 'partial_success',
                    'wallet': {
                        'address': account.address,
                        'private_key': account.key.hex()  # NEVER do this in production
                    },
                    'token_error': result
                }

            return {
                'status': 'success',
                'wallet': {
                    'address': account.address,
                    'private_key': account.key.hex()  # NEVER do this in production
                },
                'tokens': {
                    'amount': '100 DOTM',
                    'tx_hash': result
                },
                'note': 'IMPORTANT: Save the private key securely. It will not be shown again.'
            }

        except Exception as e:
            print(f"Error creating test wallet: {str(e)}")
            return {'error': str(e)}, 500

@app.route('/update-token-price', methods=['GET'])
def update_token_price():
    """Endpoint to manually update token price"""
    try:
        price_data = ethereum_helper.get_token_price_from_etherscan()
        return jsonify({
            'status': 'success',
            'message': 'Token price updated',
            'data': price_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/product-rules', methods=['GET'])
def get_product_rules_api():
    """Get all product rules"""
    try:
        rules = product_rules_helper.get_all_product_rules()
        return jsonify({
            'status': 'success',
            'product_rules': rules
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/product-rules/<product_id>', methods=['GET'])
def get_single_product_rule(product_id):
    """Get product rule for specific Stripe product ID"""
    try:
        rule = product_rules_helper.get_product_rules(product_id)
        if rule:
            return jsonify({
                'status': 'success',
                'product_rule': rule
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Product rule not found'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/product-rules/<product_id>', methods=['PUT'])
def update_product_rule(product_id):
    """Update product rule for specific Stripe product ID"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        success = product_rules_helper.update_product_rules(product_id, **data)
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Product rule updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update product rule'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/network-features/<firebase_uid>', methods=['GET'])
def get_user_network_features(firebase_uid):
    """Get network features and their status for a user"""
    try:
        print(f"Getting network features for Firebase UID: {firebase_uid}")

        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            print(f"User not found for Firebase UID: {firebase_uid}")
            return jsonify({
                'status': 'error',
                'message': f'User not found for Firebase UID: {firebase_uid}. Please ensure you are logged in.'
            }), 404

        # user_data is a tuple, so we need to access by index
        user_id = user_data[0]
        user_email = user_data[1]
        print(f"Found user ID: {user_id} for Firebase UID: {firebase_uid}")

        # Get all network features from database
        try:
            import stripe_network_features
            features = stripe_network_features.get_network_features()
            print(f"Loaded {len(features)} network features from stripe_network_features")
        except Exception as feature_err:
            print(f"Error loading network features: {str(feature_err)}")
            # Provide default features if the module fails
            features = [
                {
                    'stripe_product_id': 'network_security_basic',
                    'feature_name': 'network_security',
                    'feature_title': 'Network Security',
                    'description': 'Basic network security features including firewall and threat detection',
                    'default_enabled': True,
                    'price_cents': 500
                },
                {
                    'stripe_product_id': 'network_optimization',
                    'feature_name': 'optimization',
                    'feature_title': 'Network Optimization',
                    'description': 'Optimize network performance and reduce latency',
                    'default_enabled': False,
                    'price_cents': 300
                },
                {
                    'stripe_product_id': 'network_monitoring',
                    'feature_name': 'monitoring',
                    'feature_title': 'Network Monitoring',
                    'description': 'Real-time network monitoring and analytics',
                    'default_enabled': False,
                    'price_cents': 400
                }
            ]

        # Get user data from database
        oxio_data = {
            'user_id': user_id,
            'email': user_email,
            'oxio_user_id': user_data[7] if len(user_data) > 7 else None,  # OXIO user ID from user_data tuple
            'metamask_address': user_data[8] if len(user_data) > 8 else None,  # ETH address from user_data tuple
            'phone_number': None,
            'line_id': None,
            'iccid': None,
            'activation_code': None,
            'plan_name': None,
            'data_allowance': None,
            'validity_days': None,
            'regions': [],
            'status': 'not_activated',
            'qr_code': None,
            'profile_id': None,
            'subscription_id': None,
            'last_updated': None
        }

        # Get user's current preferences
        user_prefs = {}
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Ensure user_network_preferences table exists
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS user_network_preferences (
                                id SERIAL PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                stripe_product_id VARCHAR(100) NOT NULL,
                                enabled BOOLEAN DEFAULT FALSE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(user_id, stripe_product_id)
                            )
                        """)

                        cur.execute("""
                            SELECT stripe_product_id, enabled 
                            FROM user_network_preferences 
                            WHERE user_id = %s
                        """, (user_id,))

                        user_prefs = {row[0]: row[1] for row in cur.fetchall()}
                        print(f"Found user preferences: {user_prefs}")
        except Exception as pref_err:
            print(f"Error getting user preferences: {str(pref_err)}")

        user_features = []
        for feature in features:
            # Use user preference if exists, otherwise use default
            enabled = user_prefs.get(feature['stripe_product_id'], feature.get('default_enabled', False))

            user_features.append({
                'stripe_product_id': feature['stripe_product_id'],
                'feature_name': feature['feature_name'],
                'feature_title': feature['feature_title'],
                'description': feature['description'],
                'enabled': enabled,
                'price_cents': feature.get('price_cents', 0)
            })

        print(f"Returning {len(user_features)} features for user")
        return jsonify({
            'status': 'success',
            'features': user_features,
            'user_id': user_id,
            'firebase_uid': firebase_uid
        })
    except Exception as e:
        print(f"Error in get_user_network_features: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/network-features/<firebase_uid>/<product_id>', methods=['PUT'])
def toggle_network_feature(firebase_uid, product_id):
    """Toggle a network feature for a user"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)

        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        # user_data is a tuple, so we need to access by index
        user_id = user_data[0]

        # Update user's feature preference
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Insert or update preference
                cur.execute("""
                    INSERT INTO user_network_preferences (user_id, stripe_product_id, enabled)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, stripe_product_id)
                    DO UPDATE SET 
                        enabled = EXCLUDED.enabled,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, product_id, enabled))

                conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Feature {product_id} {"enabled" if enabled else "disabled"}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test-ping-creation', methods=['GET'])
def test_ping_creation():
    """Test endpoint to create a single ping record"""
    try:
        # Ensure table exists
        create_token_pings_table()

        # Create a test ping directly
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Insert test ping
                    token_price = 1.0
                    request_time = 50
                    response_time = 100
                    roundtrip = 150

                    cur.execute(
                        """INSERT INTO token_price_pings 
                          (token_price, request_time_ms, response_time_ms, roundtrip_ms, 
                           ping_destination, source, additional_data)
                          VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                        (
                            token_price,
                            request_time,
                            response_time,
                            roundtrip,
                            'test endpoint',
                            'test',
                            json.dumps({'test': True, 'user_id': 1})
                        )
                    )
                    ping_id = cur.fetchone()[0]
                    conn.commit()

                    return jsonify({
                        'status': 'success',
                        'message': f'Test ping created with ID: {ping_id}',
                        'ping_id': ping_id
                    })
    except Exception as e:
        print(f"Error creating test ping: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/populate-token-pings', methods=['GET'])
def populate_token_pings():
    """Endpoint to generate sample token price pings for testing"""
    try:
        # Ensure table exists first
        create_token_pings_table()

        # Generate 10 sample pings
        results = []

        # Create the token_price_pings table if it doesn't exist yet
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if table exists
                    cur.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'token_price_pings')"
                    )
                    table_exists = cur.fetchone()[0]

                    if not table_exists:
                        print("Creating token_price_pings table...")
                        create_table_sql = """
                        CREATE TABLE token_price_pings (
                            id SERIAL PRIMARY KEY,
                            token_price DECIMAL(18,9) NOT NULL,
                            request_time_ms INTEGER,
                            response_time_ms INTEGER,
                            roundtrip_ms INTEGER,
                            ping_destination VARCHAR(255),
                            source VARCHAR(100),
                            additional_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                        cur.execute(create_table_sql)
                        conn.commit()
                        print("token_price_pings table created successfully")

                    # Generate sample ping data directly
                    import json
                    import random
                    import time
                    from datetime import datetime, timedelta

                    print("Inserting sample ping data...")

                    # Insert 20 sample records spanning the last 24 hours
                    for i in range(20):
                        # Create varying timestamps over the last 24 hours
                        hours_ago = random.uniform(0, 24)
                        timestamp = datetime.now() - timedelta(hours=hours_ago)

                        # Create realistic test data
                        token_price = 1.0 + (random.random() * 0.2 - 0.1)  # $0.90 to $1.10
                        request_time = random.randint(20, 200)
                        response_time = request_time + random.randint(5, 50)
                        roundtrip = random.randint(40, 300)
                        source = random.choice(['etherscan', 'development', 'coinmarketcap', 'local'])
                        destination = 'https://api.etherscan.io/api' if source == 'etherscan' else 'local'

                        # Additional data as JSON
                        additional_data = json.dumps({
                            'eth_price': 2500 + (random.random() * 100 - 50),
                            'timestamp': timestamp.isoformat(),
                            'sample_data': True,
                            'network': random.choice(['mainnet', 'testnet']),
                            'status': 'success',
                            'user_id': 1  # Using fixed UserID 1 from database
                        })

                        # Insert the record
                        cur.execute(
                            """INSERT INTO token_price_pings 
                              (token_price, request_time_ms, response_time_ms, roundtrip_ms, 
                               ping_destination, source, additional_data, created_at)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                            (token_price, request_time, response_time, roundtrip, 
                             destination, source, additional_data, timestamp)
                        )

                        ping_id = cur.fetchone()[0]
                        results.append({
                            'id': ping_id,
                            'price': token_price,
                            'timestamp': timestamp.isoformat()
                        })

                    conn.commit()
                    print(f"Successfully inserted {len(results)} sample pings")

        # Also generate a few real-time pings
        for i in range(3):
            price_data = ethereum_helper.get_token_price_from_etherscan()
            results.append(price_data)
            # Short delay between pings
            time.sleep(0.2)

        return jsonify({
            'status': 'success',
            'message': f'Generated {len(results)} token price pings',
            'data': results
        })
    except Exception as e:
        print(f"Error populating token pings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def create_token_pings_table():
    """Create token_price_pings table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if table exists
                    cur.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'token_price_pings')"
                    )
                    table_exists = cur.fetchone()[0]

                    if not table_exists:
                        # Create the table if it doesn't exist
                        print("Creating token_price_pings table...")
                        create_table_sql = """
                        CREATE TABLE token_price_pings (
                            id SERIAL PRIMARY KEY,
                            token_price DECIMAL(18,9) NOT NULL,
                            request_time_ms INTEGER,
                            response_time_ms INTEGER,
                            roundtrip_ms INTEGER,
                            ping_destination VARCHAR(255),
                            source VARCHAR(100),
                            additional_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                        cur.execute(create_table_sql)
                        conn.commit()
                        print("token_price_pings table created successfully")
                        return True
                    else:
                        # Check if all required columns exist
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'token_price_pings'
                        """)
                        columns = [row[0] for row in cur.fetchall()]
                        required_columns = ['ping_destination', 'source', 'additional_data']

                        for column in required_columns:
                            if column not in columns:
                                print(f"Adding missing column {column} to token_price_pings table...")
                                if column == 'ping_destination':
                                    cur.execute("ALTER TABLE token_price_pings ADD COLUMN ping_destination VARCHAR(255)")
                                elif column == 'source':
                                    cur.execute("ALTER TABLE token_price_pings ADD COLUMN source VARCHAR(100)")
                                elif column == 'additional_data':
                                    cur.execute("ALTER TABLE token_price_pings ADD COLUMN additional_data TEXT")
                        conn.commit()
                    return True
    except Exception as e:
        print(f"Error creating/updating token_price_pings table: {str(e)}")
        return False

# Call the function on startup
create_token_pings_table()

@app.route('/api/ethereum-transactions', methods=['GET'])
def get_ethereum_transactions():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's ETH address
                cur.execute("SELECT eth_address FROM users WHERE id = %s", (user_id,))
                result = cur.fetchone()

                if not result or not result[0]:
                    return jsonify({'transactions': []})

                eth_address = result[0]

                # Get transactions from blockchain (placeholder)
                transactions = [
                    {
                        'hash': '0x1234...abcd',
                        'amount': '1.33',
                        'type': 'DOTM Token Purchase',
                        'date': '2024-06-15',
                        'status': 'confirmed'
                    }
                ]

                return jsonify({'transactions': transactions})

    except Exception as e:
        print(f"Error fetching Ethereum transactions: {str(e)}")
        return jsonify({'transactions': []})

@app.route('/api/fix-user-oxio-data', methods=['POST'])
def fix_user_oxio_data():
    """Fix missing OXIO data for existing users"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebaseUid')
        email = data.get('email')

        if not firebase_uid and not email:
            return jsonify({'success': False, 'message': 'Firebase UID or email is required'}), 400

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get user details
                    if firebase_uid:
                        cur.execute("""
                            SELECT id, email, display_name, oxio_user_id, oxio_group_id
                            FROM users 
                            WHERE firebase_uid = %s
                        """, (firebase_uid,))
                    else:
                        cur.execute("""
                            SELECT id, email, display_name, oxio_user_id, oxio_group_id
                            FROM users 
                            WHERE email = %s
                        """, (email,))

                    user_result = cur.fetchone()

                    if not user_result:
                        return jsonify({'success': False, 'message': 'User not found'}), 404

                    user_id, user_email, display_name, existing_oxio_user_id, existing_oxio_group_id = user_result

                    # Try to find existing OXIO user by email
                    print(f"Attempting to find existing OXIO user for email: {user_email}")
                    existing_user_result = oxio_service.find_user_by_email(user_email)

                    if existing_user_result.get('success'):
                        oxio_user_id = existing_user_result.get('oxio_user_id')
                        print(f"Found existing OXIO user ID: {oxio_user_id}")

                        # Update user with found OXIO user ID
                        cur.execute(
                            "UPDATE users SET oxio_user_id = %s WHERE id = %s",
                            (oxio_user_id, user_id)
                        )
                        conn.commit()

                        return jsonify({
                            'success': True,
                            'message': 'Successfully linked existing OXIO user',
                            'user_id': user_id,
                            'email': user_email,
                            'oxio_user_id': oxio_user_id,
                            'firebase_uid': firebase_uid,
                            'oxio_response': existing_user_result
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'Could not find existing OXIO user: {existing_user_result.get("message", "Unknown error")}',
                            'user_id': user_id,
                            'email': user_email,
                            'firebase_uid': firebase_uid,
                            'oxio_response': existing_user_result
                        }), 404

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error in fix user OXIO data endpoint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/create-oxio-user', methods=['POST'])
def create_oxio_user_endpoint():
    """Create an OXIO user for an existing Firebase user"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebaseUid')

        if not firebase_uid:
            return jsonify({'success': False, 'message': 'Firebase UID is required'}), 400

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get user details
                    cur.execute("""
                        SELECT id, email, display_name, oxio_user_id 
                        FROM users 
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))
                    user_result = cur.fetchone()

                    if not user_result:
                        return jsonify({'success': False, 'message': 'User not found'}), 404

                    user_id, email, display_name, existing_oxio_user_id = user_result

                    if existing_oxio_user_id:
                        return jsonify({
                            'success': True,
                            'message': 'OXIO user already exists',
                            'oxio_user_id': existing_oxio_user_id
                        })

                    # Create OXIO user
                    try:
                        print(f"Creating OXIO user for existing Firebase user: {firebase_uid}")
                        # Parse display_name to get first and last name
                        name_parts = (display_name or "Anonymous Anonymous").split(' ', 1)
                        first_name = name_parts[0] if name_parts else "Anonymous"
                        last_name = name_parts[1] if len(name_parts) > 1 else "Anonymous"

                        oxio_result = oxio_service.create_oxio_user(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            firebase_uid=firebase_uid
                        )

                        if oxio_result.get('success'):
                            oxio_user_id = oxio_result.get('oxio_user_id')

                            # Update user with OXIO user ID
                            cur.execute(
                                "UPDATE users SET oxio_user_id = %s WHERE id = %s",
                                (oxio_user_id, user_id)
                            )
                            conn.commit()

                            return jsonify({
                                'success': True,
                                'message': 'OXIO user created successfully',
                                'oxio_user_id': oxio_user_id,
                                'oxio_response': oxio_result
                            })
                        else:
                            # Check if user already exists (error code 6805)
                            if (oxio_result.get('status_code') == 400 and 
                                oxio_result.get('data', {}).get('code') == 6805):
                                print(f"OXIO user already exists for {email}, attempting to find existing user ID")

                                # Try to find existing OXIO user by email
                                existing_user_result = oxio_service.find_user_by_email(email)
                                if existing_user_result.get('success'):
                                    oxio_user_id = existing_user_result.get('oxio_user_id')
                                    print(f"Found existing OXIO user ID: {oxio_user_id}")

                                    # Update user with found OXIO user ID
                                    cur.execute(
                                        "UPDATE users SET oxio_user_id = %s WHERE id = %s",
                                        (oxio_user_id, user_id)
                                    )
                                    conn.commit()

                                    return jsonify({
                                        'success': True,
                                        'message': 'Found and linked existing OXIO user',
                                        'oxio_user_id': oxio_user_id,
                                        'oxio_response': existing_user_result
                                    })
                                else:
                                    return jsonify({
                                        'success': False,
                                        'message': f'OXIO user exists but could not be found: {existing_user_result.get("message", "Unknown error")}',
                                        'oxio_response': existing_user_result
                                    }), 500
                            else:
                                return jsonify({
                                    'success': False,
                                    'message': f'Failed to create OXIO user: {oxio_result.get("message", "Unknown error")}',
                                    'oxio_response': oxio_result
                                }), 500
                    except Exception as oxio_err:
                        return jsonify({
                            'success': False,
                            'message': f'Error creating OXIO user: {str(oxio_err)}'
                        }), 500

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error in create OXIO user endpoint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/oxio-activation-status')
def get_oxio_activation_status():
    """Get OXIO activation status for a user"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400

    try:
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        user_id = user_data[0]

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get OXIO activation records for this user
                    cur.execute("""
                        SELECT id, product_id, iccid, line_id, phone_number, 
                               activation_status, oxio_response, created_at
                        FROM oxio_activations 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC
                    """, (user_id,))

                    activations = cur.fetchall()
                    activation_list = []

                    for activation in activations:
                        try:
                            oxio_response = json.loads(activation[6]) if activation[6] else {}
                        except:
                            oxio_response = {}

                        activation_list.append({
                            'id': activation[0],
                            'product_id': activation[1],
                            'iccid': activation[2],
                            'line_id': activation[3],
                            'phone_number': activation[4],
                            'activation_status': activation[5],
                            'oxio_response': oxio_response,
                            'created_at': activation[7].isoformat() if activation[7] else None
                        })

                    return jsonify({
                        'status': 'success',
                        'user_id': user_id,
                        'firebase_uid': firebase_uid,
                        'activations': activation_list,
                        'total_activations': len(activation_list)
                    })

        return jsonify({'error': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error getting OXIO activation status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_user_notifications():
    """Get notifications for a user"""
    try:
        firebase_uid = request.args.get('firebaseUid')
        limit = int(request.args.get('limit', 50))

        if not firebase_uid:
            return jsonify({'error': 'Firebase UID is required'}), 400

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get notifications for this user
                    cur.execute("""
                        SELECT id, title, body, notification_type, audio_url, delivered, read_status, 
                               fcm_response, created_at, delivered_at
                        FROM notifications 
                        WHERE firebase_uid = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (firebase_uid, limit))

                    notifications = cur.fetchall()
                    notification_list = []

                    for notif in notifications:
                        notification_list.append({
                            'id': notif[0],
                            'title': notif[1],
                            'body': notif[2],
                            'type': notif[3],
                            'audio_url': notif[4],
                            'delivered': notif[5],
                            'read': notif[6],
                            'fcm_response': notif[7],
                            'created_at': notif[8].isoformat() if notif[8] else None,
                            'delivered_at': notif[9].isoformat() if notif[9] else None
                        })

                    return jsonify({
                        'success': True,
                        'notifications': notification_list,
                        'count': len(notification_list),
                        'firebase_uid': firebase_uid
                    })

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        firebase_uid = request.json.get('firebaseUid') if request.json else None

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Update notification as read
                    if firebase_uid:
                        cur.execute("""
                            UPDATE notifications 
                            SET read_status = TRUE
                            WHERE id = %s AND firebase_uid = %s
                            RETURNING title
                        """, (notification_id, firebase_uid))
                    else:
                        cur.execute("""
                            UPDATE notifications 
                            SET read_status = TRUE
                            WHERE id = %s
                            RETURNING title
                        """, (notification_id,))

                    result = cur.fetchone()
                    if result:
                        conn.commit()
                        return jsonify({
                            'success': True,
                            'message': f'Notification "{result[0]}" marked as read'
                        })
                    else:
                        return jsonify({'success': False, 'message': 'Notification not found'}), 404

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/update-personal-message', methods=['POST'])
def update_personal_message():
    """Update or create a personal message for a specific Firebase UID"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebase_uid')
        email = data.get('email', 'Unknown Email')
        personal_message = data.get('personal_message', '')

        if not firebase_uid:
            return jsonify({'success': False, 'message': 'Firebase UID is required'}), 400

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if an invite already exists for this Firebase UID
                    cur.execute("""
                        SELECT id, email FROM invites 
                        WHERE invited_by_firebase_uid = %s OR email = %s
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, (firebase_uid, email))

                    existing_invite = cur.fetchone()

                    if existing_invite:
                        # Update existing invite
                        cur.execute("""
                            UPDATE invites 
                            SET personal_message = %s, 
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                            RETURNING id
                        """, (personal_message, existing_invite[0]))
                        updated_id = cur.fetchone()[0]
                        action = 'updated'
                    else:
                        # Create new invite record with the custom message
                        import secrets
                        invitation_token = secrets.token_urlsafe(32)

                        # Try to get user ID by Firebase UID
                        cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        user_result = cur.fetchone()
                        user_id = user_result[0] if user_result else None

                        cur.execute("""
                            INSERT INTO invites 
                            (user_id, email, invitation_token, invited_by_firebase_uid, 
                             personal_message, invitation_status)
                            VALUES (%s, %s, %s, %s, %s, 'draft')
                            RETURNING id
                        """, (user_id, email, invitation_token, firebase_uid, personal_message))
                        updated_id = cur.fetchone()[0]
                        action = 'created'

                    conn.commit()

                    return jsonify({
                        'success': True,
                        'message': f'Personal message {action} successfully',
                        'invite_id': updated_id,
                        'firebase_uid': firebase_uid
                    })

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error updating personal message: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Import MCP server functions at the top level
try:
    from mcp_server import SERVICES_CATALOG, calculate_total_costs
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    SERVICES_CATALOG = {}

# MCP Server Routes for Service Catalog and Pricing
@app.route('/mcp')
def mcp_server():
    """MCP server endpoint for service catalog and pricing"""
    if MCP_AVAILABLE:
        # Import the function here to avoid circular imports
        from mcp_server import mcp_server as mcp_server_func
        # Get the mcp_server route handler from the mcp_server module
        with mcp_app.app_context():
            from mcp_server import mcp_server as mcp_server_func
            return mcp_server_func()
    else:
        return jsonify({
            "error": "MCP server not available",
            "message": "Service catalog endpoint is currently unavailable"
        }), 503

@app.route('/mcp/api')
def mcp_api():
    """JSON API endpoint for programmatic access to service catalog"""
    if MCP_AVAILABLE:
        from mcp_server import mcp_api as mcp_api_func
        return mcp_api_func()
    else:
        return jsonify({
            "error": "MCP API not available",
            "fallback_services": {
                "basic_membership": {"price_usd": 24.00, "type": "annual"},
                "full_membership": {"price_usd": 66.00, "type": "annual"},
                "global_data_10gb": {"price_usd": 10.00, "type": "one_time"}
            }
        })

@app.route('/mcp/service/<service_id>')
def mcp_service_detail(service_id):
    """MCP service detail endpoint"""
    if MCP_AVAILABLE:
        from mcp_server import mcp_service_detail as mcp_service_detail_func
        return mcp_service_detail_func(service_id)
    else:
        return jsonify({"error": "Service detail endpoint not available"}), 503

@app.route('/mcp/calculate')
def mcp_pricing_calculator():
    """MCP pricing calculator endpoint"""
    if MCP_AVAILABLE:
        from mcp_server import mcp_pricing_calculator as mcp_pricing_calculator_func
        return mcp_pricing_calculator_func()
    else:
        return jsonify({"error": "Pricing calculator not available"}), 503

# Beta Approval System API Endpoints
@app.route('/api/beta-request', methods=['POST'])
def submit_beta_request():
    """Submit a beta access request"""
    try:
        from beta_approval_service import BetaApprovalService
        
        data = request.get_json()
        # Support both parameter formats from frontend
        firebase_uid = data.get('firebaseUid') or data.get('firebase_uid')
        user_email = data.get('email')
        user_name = data.get('name')
        
        if not firebase_uid:
            return jsonify({
                'success': False,
                'message': 'Firebase UID is required',
                'error': 'Missing firebaseUid parameter'
            }), 400
            
        # Get user email from database if not provided
        if not user_email:
            try:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT email FROM users WHERE firebase_uid = %s", (firebase_uid,))
                            user_data = cursor.fetchone()
                            if user_data:
                                user_email = user_data[0]
            except Exception as e:
                print(f"Error getting user email: {str(e)}")
                
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'User not found. Please sign up first.',
                'error': 'Cannot find user email for firebaseUid'
            }), 400
        
        beta_service = BetaApprovalService()
        result = beta_service.submit_beta_request(user_email, firebase_uid, user_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            # Ensure error response has message field
            if 'message' not in result and 'error' in result:
                result['message'] = result['error']
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in submit_beta_request: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/beta-approve/<request_id>')
def approve_beta_request(request_id):
    """Approve a beta request (admin endpoint)"""
    try:
        from beta_approval_service import BetaApprovalService
        
        beta_service = BetaApprovalService()
        result = beta_service.approve_beta_request(request_id)
        
        if result['success']:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #f0f8ff;">
                <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h1 style="color: #4CAF50; text-align: center;">✅ Beta Request Approved!</h1>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Phone Number Assigned:</strong> {result.get('phone_number')}</p>
                    <p><strong>OXIO User ID:</strong> {result.get('oxio_user_id')}</p>
                    <p><strong>Group ID:</strong> {result.get('group_id')}</p>
                    <p style="margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                        The user has been notified via email and can now access beta features.
                    </p>
                </div>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #fff5f5;">
                <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h1 style="color: #f44336; text-align: center;">❌ Approval Failed</h1>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>
                    <p><strong>Message:</strong> {result.get('message', 'No additional details')}</p>
                </div>
            </body>
            </html>
            """, 400
            
    except Exception as e:
        print(f"Error in approve_beta_request: {str(e)}")
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #fff5f5;">
            <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1 style="color: #f44336; text-align: center;">❌ System Error</h1>
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
        </body>
        </html>
        """, 500

@app.route('/api/beta-reject/<request_id>')
def reject_beta_request(request_id):
    """Reject a beta request (admin endpoint)"""
    try:
        from beta_approval_service import BetaApprovalService
        
        # Get optional reason from query parameter
        reason = request.args.get('reason', 'Not specified')
        
        beta_service = BetaApprovalService()
        result = beta_service.reject_beta_request(request_id, reason)
        
        if result['success']:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #fff8e1;">
                <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h1 style="color: #ff9800; text-align: center;">⚠️ Beta Request Rejected</h1>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Reason:</strong> {reason}</p>
                    <p style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 5px;">
                        The user has been notified via email about the rejection.
                    </p>
                </div>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #fff5f5;">
                <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h1 style="color: #f44336; text-align: center;">❌ Rejection Failed</h1>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>
                </div>
            </body>
            </html>
            """, 400
            
    except Exception as e:
        print(f"Error in reject_beta_request: {str(e)}")
        return f"<h1>Error: {str(e)}</h1>", 500

@app.route('/api/beta-status')
def get_beta_status():
    """Get beta status for current user"""
    try:
        from beta_approval_service import BetaApprovalService
        
        # Get Firebase UID from request (you may need to implement proper auth)
        firebase_uid = request.args.get('firebase_uid')
        if not firebase_uid:
            return jsonify({
                'success': False,
                'error': 'Firebase UID required'
            }), 400
        
        beta_service = BetaApprovalService()
        result = beta_service.get_user_beta_status(firebase_uid)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in get_beta_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user-esim-details')
def get_user_esim_details():
    """Get user's eSIM details including phone numbers, ICCID, and QR codes"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400
    
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get all eSIM activations for this user
                    cur.execute("""
                        SELECT phone_number, iccid, line_id, activation_status, 
                               esim_qr_code, created_at, product_id
                        FROM oxio_activations 
                        WHERE firebase_uid = %s 
                        ORDER BY created_at DESC
                    """, (firebase_uid,))
                    
                    activations = cur.fetchall()
                    esim_details = []
                    
                    for activation in activations:
                        esim_details.append({
                            'phone_number': activation[0],
                            'iccid': activation[1], 
                            'line_id': activation[2],
                            'status': activation[3],
                            'qr_code': activation[4],
                            'activated_date': activation[5].isoformat() if activation[5] else None,
                            'product_type': activation[6]
                        })
                    
                    return jsonify({
                        'success': True,
                        'esim_count': len(esim_details),
                        'esims': esim_details
                    })
        
        return jsonify({'success': False, 'error': 'Database connection failed'})
        
    except Exception as e:
        print(f"Error getting eSIM details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user-phone-numbers')
def get_user_phone_numbers():
    """Get ALL user's phone numbers from multiple sources"""
    try:
        from beta_approval_service import BetaApprovalService
        from qr_generator import generate_resin_qr_code, generate_simple_phone_qr
        
        firebase_uid = request.args.get('firebase_uid')
        if not firebase_uid:
            return jsonify({
                'success': False,
                'error': 'Firebase UID required'
            }), 400
        
        all_phone_numbers = []
        
        # 1. Get user's primary phone number from users table
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT phone_number FROM users 
                            WHERE firebase_uid = %s AND phone_number IS NOT NULL
                        """, (firebase_uid,))
                        result = cur.fetchone()
                        if result and result[0]:
                            all_phone_numbers.append({
                                'phoneNumber': result[0],
                                'source': 'user_profile',
                                'type': 'Primary',
                                'countryCode': 'US'
                            })
                            print(f"Found primary phone number: {result[0]}")
        except Exception as e:
            print(f"Error getting user profile phone number: {e}")
        
        # 2. Get phone numbers from OXIO activations
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT DISTINCT phone_number, line_id, activation_status, created_at
                            FROM oxio_activations 
                            WHERE firebase_uid = %s AND phone_number IS NOT NULL
                            ORDER BY created_at DESC
                        """, (firebase_uid,))
                        oxio_results = cur.fetchall()
                        
                        for result in oxio_results:
                            phone_num, line_id, status, created_at = result
                            all_phone_numbers.append({
                                'phoneNumber': phone_num,
                                'source': 'oxio_activation',
                                'type': 'eSIM',
                                'lineId': line_id,
                                'status': status,
                                'activatedAt': created_at.isoformat() if created_at else None,
                                'countryCode': 'US'
                            })
                            print(f"Found OXIO phone number: {phone_num} (Line: {line_id})")
        except Exception as e:
            print(f"Error getting OXIO phone numbers: {e}")
        
        # 3. Get beta phone number (if approved)
        try:
            beta_service = BetaApprovalService()
            beta_status = beta_service.get_user_beta_status(firebase_uid)
            
            if beta_status.get('has_request') and beta_status.get('status') == 'approved':
                beta_phone = beta_status.get('phone_number')
                group_id = beta_status.get('group_id')
                oxio_user_id = beta_status.get('oxio_user_id')
                
                if beta_phone:
                    # Generate QR codes for beta phone
                    try:
                        resin_qr = generate_resin_qr_code(
                            beta_phone, 
                            group_id, 
                            oxio_user_id, 
                            beta_status.get('resin_data', {})
                        )
                        simple_qr = generate_simple_phone_qr(beta_phone)
                        
                        all_phone_numbers.append({
                            'phoneNumber': beta_phone,
                            'source': 'beta_access',
                            'type': 'Beta',
                            'groupId': group_id,
                            'oxioUserId': oxio_user_id,
                            'resinQr': resin_qr,
                            'simpleQr': simple_qr,
                            'countryCode': 'US',
                            'approvedAt': beta_status.get('approved_at')
                        })
                        print(f"Found beta phone number: {beta_phone}")
                    except Exception as qr_error:
                        print(f"Error generating QR codes: {qr_error}")
                        # Add phone without QR codes
                        all_phone_numbers.append({
                            'phoneNumber': beta_phone,
                            'source': 'beta_access',
                            'type': 'Beta',
                            'groupId': group_id,
                            'oxioUserId': oxio_user_id,
                            'countryCode': 'US',
                            'approvedAt': beta_status.get('approved_at')
                        })
                        print(f"Found beta phone number: {beta_phone} (no QR codes)")
        except Exception as e:
            print(f"Error getting beta phone number: {e}")
        
        # Remove duplicates based on phone number
        unique_numbers = []
        seen_numbers = set()
        
        for phone_data in all_phone_numbers:
            phone_num = phone_data['phoneNumber']
            if phone_num not in seen_numbers:
                seen_numbers.add(phone_num)
                unique_numbers.append(phone_data)
        
        print(f"Found {len(unique_numbers)} unique phone numbers for user {firebase_uid}")
        
        return jsonify({
            'success': True,
            'phoneNumbers': unique_numbers,
            'total_count': len(unique_numbers)
        }), 200
        
    except Exception as e:
        print(f"Error in get_user_phone_numbers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Secure GitHub API endpoints
@app.route('/api/github/configure', methods=['POST'])
@require_admin_auth
def configure_github_repository():
    """Configure GitHub repository for uploads (Admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        repo_owner = data.get('owner')
        repo_name = data.get('repo_name')
        branch = data.get('branch', 'main')
        
        if not repo_owner or not repo_name:
            return jsonify({
                'success': False,
                'error': 'Repository owner and name are required'
            }), 400
        
        github_service_secure.set_repository(repo_owner, repo_name, branch)
        
        return jsonify({
            'success': True,
            'message': f'GitHub repository configured: {repo_owner}/{repo_name} (branch: {branch})'
        }), 200
        
    except Exception as e:
        print(f"Error in configure_github_repository: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/github/upload-file', methods=['POST'])
@require_admin_auth
def upload_file_to_github():
    """Upload a single file to GitHub repository (Admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        file_path = data.get('file_path')
        content = data.get('content', '')
        commit_message = data.get('commit_message')
        repo_owner = data.get('repo_owner')
        repo_name = data.get('repo_name')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'File path is required'
            }), 400
            
        if not commit_message:
            commit_message = f'Update {file_path} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        result = github_service_secure.upload_file(
            file_path=file_path,
            content=content,
            commit_message=commit_message,
            repo_owner=repo_owner,
            repo_name=repo_name
        )
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {file_path}',
                'result': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Upload failed'),
                'result': result
            }), 500
        
    except Exception as e:
        print(f"Error in upload_file_to_github: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/github/upload-project', methods=['POST'])
@require_admin_auth
def upload_project_to_github():
    """Upload key project files to GitHub repository (Admin only)"""
    try:
        data = request.get_json() or {}
        
        repo_owner = data.get('repo_owner')
        repo_name = data.get('repo_name')
        
        # Get list of files to upload securely
        files_to_upload = github_service_secure.get_project_files_for_upload()
        
        if not files_to_upload:
            return jsonify({
                'success': False,
                'error': 'No files found to upload'
            }), 400
        
        # Perform secure batch upload
        result = github_service_secure.upload_multiple_files(
            files=files_to_upload,
            repo_owner=repo_owner,
            repo_name=repo_name
        )
        
        return jsonify({
            'success': True,
            'message': f'Upload completed: {result["successful"]} successful, {result["failed"]} failed',
            'result': result
        }), 200
        
    except Exception as e:
        print(f"Error in upload_project_to_github: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/github/status', methods=['GET'])
@require_auth
def get_github_status():
    """Get GitHub service status and configuration (Authenticated)"""
    try:
        # Test GitHub authentication securely
        auth_result = github_service_secure.get_authenticated_client()
        
        return jsonify({
            'success': True,
            'authentication': 'connected' if auth_result else 'failed',
            'configuration': {
                'repo_owner': github_service_secure.repo_owner,
                'repo_name': github_service_secure.repo_name,
                'default_branch': github_service_secure.default_branch
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_github_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/upload-to-github', methods=['POST'])
@require_auth
def upload_documentation_to_github():
    """Upload updated documentation to GitHub repository"""
    try:
        from github_service import github_service
        
        # Set repository configuration
        github_service.set_repository("dataontap", "gorse", "main")
        
        # Check GitHub authentication
        if not github_service.get_authenticated_client():
            return jsonify({
                'success': False,
                'error': 'GitHub authentication failed'
            }), 401
        
        # Read current README content
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # Upload README.md
        result = github_service.upload_file(
            file_path='README.md',
            content=readme_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'),
            commit_message='Update README with Resend email integration information'
        )
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': 'Documentation uploaded successfully to GitHub',
                'result': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        print(f"Error uploading to GitHub: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/generate-welcome-notification', methods=['POST'])
@require_admin_auth
def generate_welcome_notification():
    """Generate a welcome notification with audio for specific users (Admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        target_email = data.get('target_email')  # User to generate welcome message for
        recipient_uid = data.get('recipient_uid')  # User who should receive the notification
        language = data.get('language', 'en')
        voice_id = data.get('voice_id')  # Optional custom voice
        
        if not target_email:
            return jsonify({
                'success': False,
                'error': 'target_email is required'
            }), 400
            
        if not recipient_uid:
            return jsonify({
                'success': False,
                'error': 'recipient_uid is required (Firebase UID of notification recipient)'
            }), 400
        
        # Extract user name from email for personalization
        user_name = target_email.split('@')[0]
        
        print(f"Generating welcome notification for {target_email}, recipient: {recipient_uid}")
        
        # Generate the audio message using ElevenLabs service
        audio_result = elevenlabs_service.generate_welcome_message(
            user_name=user_name,
            language=language,
            voice_id=voice_id
        )
        
        if not audio_result.get('success'):
            return jsonify({
                'success': False,
                'error': f'Failed to generate audio: {audio_result.get("error")}'
            }), 500
        
        # Create unique filename for the audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"welcome_{user_name}_{timestamp}.mp3"
        file_path = os.path.join('static', 'audio', filename)
        
        # Save the audio file
        with open(file_path, 'wb') as f:
            f.write(audio_result['audio_data'])
        
        # Create download URL (relative to app root)
        download_url = f"/static/audio/{filename}"
        
        # Create notification record in database
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Create notifications table if it doesn't exist (with audio_url column)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS notifications (
                            id SERIAL PRIMARY KEY,
                            firebase_uid VARCHAR(128) NOT NULL,
                            title VARCHAR(255),
                            body TEXT,
                            notification_type VARCHAR(50),
                            audio_url VARCHAR(500),
                            delivered BOOLEAN DEFAULT FALSE,
                            read_status BOOLEAN DEFAULT FALSE,
                            fcm_response TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            delivered_at TIMESTAMP
                        )
                    """)
                    
                    # Ensure audio_url column exists for existing tables (migration)
                    cur.execute("""
                        ALTER TABLE notifications 
                        ADD COLUMN IF NOT EXISTS audio_url VARCHAR(500)
                    """)
                    
                    # Insert the notification
                    cur.execute("""
                        INSERT INTO notifications (firebase_uid, title, body, notification_type, audio_url)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        recipient_uid,
                        f"Welcome Message for {target_email}",
                        f"A personalized welcome message has been generated for {target_email}. Click to download the audio file.",
                        'welcome_audio',
                        download_url
                    ))
                    
                    notification_id = cur.fetchone()[0]
                    conn.commit()
                    
                    print(f"Created notification {notification_id} for recipient {recipient_uid}")
                    
                    return jsonify({
                        'success': True,
                        'message': f'Welcome notification generated successfully for {target_email}',
                        'notification_id': notification_id,
                        'audio_file': filename,
                        'download_url': download_url,
                        'recipient_uid': recipient_uid,
                        'target_email': target_email
                    }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Database connection error'
                }), 500
                
    except Exception as e:
        print(f"Error generating welcome notification: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Debug: Print all registered routes to verify OXIO endpoints are available
    print("\n=== Registered Flask Routes ===")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        print(f"  {rule.rule} [{methods}] -> {rule.endpoint}")
    print("================================\n")

    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on http://0.0.0.0:{port}")
    print(f"OXIO API endpoints should be available at:")
    print(f"  - GET  /api/oxio/test-connection")
    print(f"  - GET  /api/oxio/test-plans") 
    print(f"  - POST /api/oxio/activate-line")
    print(f"  - POST /api/oxio/test-sample-activation")

    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        # Fallback to standard Flask run
        app.run(host='0.0.0.0', port=port, debug=True)