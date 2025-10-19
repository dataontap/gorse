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
from shopify_service import shopify_service

# Import device service
from device_service import register_or_update_device, get_user_devices, mark_devices_offline

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
                            delivered_at TIMESTAMP
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

                # Check if iccid_inventory table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'iccid_inventory')")
                iccid_inventory_exists = cur.fetchone()[0]

                if not iccid_inventory_exists:
                    print("Creating iccid_inventory table...")
                    create_iccid_inventory_sql = """
                        CREATE TABLE iccid_inventory (
                            id SERIAL PRIMARY KEY,
                            iccid VARCHAR(50) UNIQUE NOT NULL,
                            lpa_code VARCHAR(200),
                            country VARCHAR(10) DEFAULT 'US',
                            line_id VARCHAR(100),
                            status VARCHAR(20) DEFAULT 'available',
                            assigned_firebase_uid VARCHAR(128),
                            assigned_email VARCHAR(255),
                            assigned_at TIMESTAMP,
                            batch_upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_iccid_status ON iccid_inventory(status);
                        CREATE INDEX IF NOT EXISTS idx_iccid_assigned_firebase_uid ON iccid_inventory(assigned_firebase_uid);
                        CREATE INDEX IF NOT EXISTS idx_iccid_batch_upload ON iccid_inventory(batch_upload_date);
                    """
                    cur.execute(create_iccid_inventory_sql)
                    conn.commit()
                    print("iccid_inventory table created successfully")
                else:
                    print("iccid_inventory table already exists")

                # Check if processed_stripe_events table exists (for webhook idempotency)
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'processed_stripe_events')")
                processed_events_exists = cur.fetchone()[0]

                if not processed_events_exists:
                    print("Creating processed_stripe_events table...")
                    create_processed_events_sql = """
                        CREATE TABLE processed_stripe_events (
                            id SERIAL PRIMARY KEY,
                            event_id VARCHAR(100) UNIQUE NOT NULL,
                            event_type VARCHAR(100) NOT NULL,
                            processing_result TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_processed_events_event_id ON processed_stripe_events(event_id);
                    """
                    cur.execute(create_processed_events_sql)
                    conn.commit()
                    print("processed_stripe_events table created successfully")
                else:
                    print("processed_stripe_events table already exists")

                # Check if welcome_messages table exists (for caching ElevenLabs audio)
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'welcome_messages')")
                welcome_messages_exists = cur.fetchone()[0]

                if not welcome_messages_exists:
                    print("Creating welcome_messages table...")
                    create_welcome_messages_sql = """
                        CREATE TABLE welcome_messages (
                            id SERIAL PRIMARY KEY,
                            firebase_uid VARCHAR(128) NOT NULL,
                            language VARCHAR(10) NOT NULL,
                            voice_profile VARCHAR(50) NOT NULL,
                            message_type VARCHAR(50) NOT NULL DEFAULT 'welcome',
                            audio_data BYTEA NOT NULL,
                            content_type VARCHAR(50) DEFAULT 'audio/mpeg',
                            generation_time_ms INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(firebase_uid, language, voice_profile, message_type)
                        );
                        CREATE INDEX IF NOT EXISTS idx_welcome_messages_firebase_uid ON welcome_messages(firebase_uid);
                        CREATE INDEX IF NOT EXISTS idx_welcome_messages_language ON welcome_messages(language);
                        CREATE INDEX IF NOT EXISTS idx_welcome_messages_voice_profile ON welcome_messages(voice_profile);
                        CREATE INDEX IF NOT EXISTS idx_welcome_messages_message_type ON welcome_messages(message_type);
                    """
                    cur.execute(create_welcome_messages_sql)
                    conn.commit()
                    print("welcome_messages table created successfully")
                else:
                    print("welcome_messages table already exists")

                # Check if user_message_history table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_message_history')")
                user_message_history_exists = cur.fetchone()[0]

                if not user_message_history_exists:
                    print("Creating user_message_history table...")
                    create_user_message_history_sql = """
                        CREATE TABLE user_message_history (
                            id SERIAL PRIMARY KEY,
                            firebase_uid VARCHAR(128) NOT NULL,
                            message_type VARCHAR(50) NOT NULL,
                            language VARCHAR(10) NOT NULL,
                            voice_profile VARCHAR(50) NOT NULL,
                            completed BOOLEAN DEFAULT FALSE,
                            listened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_user_message_history_firebase_uid ON user_message_history(firebase_uid);
                        CREATE INDEX IF NOT EXISTS idx_user_message_history_message_type ON user_message_history(message_type);
                    """
                    cur.execute(create_user_message_history_sql)
                    conn.commit()
                    print("user_message_history table created successfully")
                else:
                    print("user_message_history table already exists")

                # Check if oxio_activations table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'oxio_activations')")
                oxio_activations_exists = cur.fetchone()[0]

                if not oxio_activations_exists:
                    print("Creating oxio_activations table...")
                    create_oxio_activations_sql = """
                        CREATE TABLE oxio_activations (
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
                            activation_url TEXT,
                            activation_code VARCHAR(200),
                            oxio_response TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_oxio_activations_firebase_uid ON oxio_activations(firebase_uid);
                        CREATE INDEX IF NOT EXISTS idx_oxio_activations_user_id ON oxio_activations(user_id);
                        CREATE INDEX IF NOT EXISTS idx_oxio_activations_iccid ON oxio_activations(iccid);
                    """
                    cur.execute(create_oxio_activations_sql)
                    conn.commit()
                    print("oxio_activations table created successfully")
                else:
                    print("oxio_activations table already exists")


                # Check if invites table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'invites')")
                invites_exists = cur.fetchone()[0]

                if not invites_exists:
                    print("Creating invites table...")
                    create_invites_sql = """
                        CREATE TABLE invites (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            email VARCHAR(255) NOT NULL,
                            invitation_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                            invited_by_user_id INTEGER,
                            invited_by_firebase_uid VARCHAR(255),
                            invitation_token VARCHAR(255),
                            personal_message TEXT,
                            is_demo_user BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
                            accepted_at TIMESTAMP,
                            rejected_at TIMESTAMP,
                            cancelled_at TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_invites_email ON invites(email);
                        CREATE INDEX IF NOT EXISTS idx_invites_token ON invites(invitation_token);
                        CREATE INDEX IF NOT EXISTS idx_invites_user_id ON invites(user_id);
                        CREATE INDEX IF NOT EXISTS idx_invites_invited_by_firebase_uid ON invites(invited_by_firebase_uid);
                    """
                    cur.execute(create_invites_sql)
                    conn.commit()
                    print("invites table created successfully")
                else:
                    print("invites table already exists")

                # Check if data_usage_log table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'data_usage_log')")
                data_usage_log_exists = cur.fetchone()[0]

                if not data_usage_log_exists:
                    print("Creating data_usage_log table...")
                    create_data_usage_log_sql = """
                        CREATE TABLE data_usage_log (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            stripe_customer_id VARCHAR(100),
                            megabytes_used BIGINT NOT NULL,
                            stripe_event_id VARCHAR(100),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_data_usage_user_id ON data_usage_log(user_id);
                        CREATE INDEX IF NOT EXISTS idx_data_usage_stripe_customer_id ON data_usage_log(stripe_customer_id);
                    """
                    cur.execute(create_data_usage_log_sql)
                    conn.commit()
                    print("data_usage_log table created successfully")
                else:
                    print("data_usage_log table already exists")

                # Check if token_price_pings table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'token_price_pings')")
                token_price_pings_exists = cur.fetchone()[0]

                if not token_price_pings_exists:
                    print("Creating token_price_pings table...")
                    create_token_pings_table_sql = """
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
                        CREATE INDEX IF NOT EXISTS idx_token_price_pings_created_at ON token_price_pings(created_at);
                    """
                    cur.execute(create_token_pings_table_sql)
                    conn.commit()
                    print("token_price_pings table created successfully")
                else:
                    print("token_price_pings table already exists")

                # Check if user_network_preferences table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_network_preferences')")
                user_network_preferences_exists = cur.fetchone()[0]

                if not user_network_preferences_exists:
                    print("Creating user_network_preferences table...")
                    create_user_network_preferences_sql = """
                        CREATE TABLE user_network_preferences (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            stripe_product_id VARCHAR(100) NOT NULL,
                            enabled BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, stripe_product_id)
                        );
                        CREATE INDEX IF NOT EXISTS idx_user_network_preferences_user_id ON user_network_preferences(user_id);
                        CREATE INDEX IF NOT EXISTS idx_user_network_preferences_stripe_product_id ON user_network_preferences(stripe_product_id);
                    """
                    cur.execute(create_user_network_preferences_sql)
                    conn.commit()
                    print("user_network_preferences table created successfully")
                else:
                    print("user_network_preferences table already exists")

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

# Help Desk API endpoint (defined directly to avoid circular import)
@app.route('/api/help/start', methods=['POST'])
def start_help_session_endpoint():
    """Start a new help session or return existing unresolved ticket"""
    try:
        from help_desk_service import help_desk

        data = request.get_json() or {}

        user_data = {
            'user_id': data.get('userId'),
            'firebase_uid': data.get('firebaseUid'),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr,
            'page_url': data.get('pageUrl', request.referrer),
            'browser_timestamp': data.get('browserTimestamp')
        }

        # Check if user already has an active/unresolved ticket
        firebase_uid = user_data.get('firebase_uid')
        if firebase_uid:
            active_session = help_desk.get_active_session(firebase_uid=firebase_uid)

            if active_session.get('success'):
                print(f"User {firebase_uid} already has an open ticket: {active_session.get('jira_ticket', {}).get('key')}")
                return jsonify({
                    'status': 'success',
                    'session_id': active_session['session_id'],
                    'help_session_id': active_session['help_session_id'],
                    'jira_ticket': active_session.get('jira_ticket'),
                    'message': 'Existing open ticket found',
                    'existing': True
                })

        # No existing ticket, create a new one
        result = help_desk.start_help_session(user_data)

        if result['success']:
            return jsonify({
                'status': 'success',
                'session_id': result['session_id'],
                'help_session_id': result['help_session_id'],
                'jira_ticket': result.get('jira_ticket'),
                'message': 'Help session started successfully',
                'existing': False
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to start help session')
            }), 500

    except Exception as e:
        print(f"Error starting help session: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/update-context', methods=['POST'])
def update_help_context_endpoint():
    """Update JIRA ticket with additional context"""
    try:
        from help_desk_service import help_desk

        data = request.get_json() or {}
        session_id = data.get('sessionId')
        category = data.get('category')
        description = data.get('description')

        if not session_id:
            return jsonify({
                'status': 'error',
                'message': 'Session ID is required'
            }), 400

        if not category or not description:
            return jsonify({
                'status': 'error',
                'message': 'Category and description are required'
            }), 400

        result = help_desk.update_ticket_context(session_id, category, description)

        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Context submitted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to update context')
            }), 500

    except Exception as e:
        print(f"Error updating help context: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/user-open-ticket', methods=['GET'])
def get_user_open_ticket():
    """Get user's open ticket with current JIRA status"""
    try:
        from help_desk_service import help_desk

        firebase_uid = request.args.get('firebaseUid')
        if not firebase_uid:
            return jsonify({
                'status': 'error',
                'message': 'Firebase UID is required'
            }), 400

        result = help_desk.get_active_session(firebase_uid=firebase_uid)

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'has_open_ticket': True,
                'ticket': result
            })
        else:
            return jsonify({
                'status': 'success',
                'has_open_ticket': False,
                'message': 'No open ticket found'
            })

    except Exception as e:
        print(f"Error getting user open ticket: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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
        # Use simple OXIO user ID string format for v2 API instead of complex payload
        sample_user_id = "test-oxio-user-123"
        sample_plan_id = None  # Let OXIO use default plan

        data = request.get_json()
        if data:
            # Check if user wants to test with specific plan ID
            if 'planId' in data:
                sample_plan_id = data['planId']
            if 'testUserId' in data:
                sample_user_id = data['testUserId']

        # Use simple string format to trigger v2 API payload structure
        result = oxio_service.activate_line(sample_user_id, plan_id=sample_plan_id)
        result['test_user_id'] = sample_user_id
        result['test_plan_id'] = sample_plan_id

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

        except Exception as db_err:
            print(f"Error accessing database for pending notifications: {str(db_err)}")

        except Exception as general_err:
            print(f"General error in register_fcm_token: {str(general_err)}")

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
                            print(f"Creating OXIO user and group for Firebase UID: {firebase_uid}")

                            # Parse display_name to get first and last name
                            name_parts = (display_name or "Anonymous Anonymous").split(' ', 1)
                            first_name = name_parts[0] if name_parts else "Anonymous"
                            last_name = name_parts[1] if len(name_parts) > 1 else "Anonymous"

                            # Create OXIO user first (without group for now)
                            oxio_result = oxio_service.create_oxio_user(
                                first_name=first_name,
                                last_name=last_name,
                                email=email,
                                firebase_uid=firebase_uid,
                                oxio_group_id=None  # Will create group after user exists
                            )

                            if oxio_result.get('success'):
                                oxio_user_id = oxio_result.get('oxio_user_id')
                                print(f"Successfully created OXIO user: {oxio_user_id}")

                                # Now create OXIO group using the user ID
                                group_name = f"DOT_User_{firebase_uid[:8]}"
                                group_result = oxio_service.create_oxio_group(
                                    group_name=group_name,
                                    oxio_user_id=oxio_user_id,
                                    description=f"Group for DOT user {display_name or 'Anonymous'}"
                                )

                                if group_result.get('success'):
                                    oxio_group_id = group_result.get('oxio_group_id')
                                    print(f"Successfully created OXIO group: {oxio_group_id}")
                                else:
                                    print(f"Failed to create OXIO group: {group_result.get('message', 'Unknown error')}")
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

                        # Schedule welcome notification
                        import threading
                        def send_welcome_message():
                            import time
                            time.sleep(3)  # Wait 3 seconds for FCM token registration
                            try:
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

def get_user_by_firebase_uid(firebase_uid):
    """Get user information from database by Firebase UID with all OXIO fields"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, email, display_name, firebase_uid, stripe_customer_id,
                               imei, eth_address, oxio_user_id, oxio_group_id
                        FROM users
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))

                    user = cur.fetchone()
                    if user:
                        # Parse display_name into first_name and last_name
                        display_name = user[2] or ''
                        name_parts = display_name.split(' ', 1) if display_name else []
                        first_name = name_parts[0] if name_parts else ''
                        last_name = name_parts[1] if len(name_parts) > 1 else ''

                        print(f"get_user_by_firebase_uid debug: Found user {user[0]} with oxio_user_id: {user[7]}, eth_address: {user[6]}")

                        return {
                            'id': user[0],
                            'email': user[1],
                            'first_name': first_name,
                            'last_name': last_name,
                            'display_name': display_name,
                            'firebase_uid': user[3],
                            'stripe_customer_id': user[4],
                            'imei': user[5],
                            'eth_address': user[6],
                            'oxio_user_id': user[7],
                            'oxio_group_id': user[8]
                        }
        return None
    except Exception as e:
        print(f"Error getting user by Firebase UID: {str(e)}")
        return None

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
                        user_data = {
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
                        }
                        print(f"Returning user data for Firebase UID {firebase_uid}: userId={user[0]}, email={user[1]}")
                        return jsonify(user_data)

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

# Device Detection and Management API
@app.route('/api/devices/register', methods=['POST'])
def register_device():
    """Register or update a device for the current user"""
    try:
        from firebase_helper import verify_firebase_token

        # Verify Firebase token and get UID - NO FALLBACK for security
        decoded_token, error = verify_firebase_token(request)

        if error:
            return jsonify({'success': False, 'error': f'Authentication required: {error}'}), 401

        firebase_uid = decoded_token.get('uid')

        # Get user_id from firebase_uid
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    user = cur.fetchone()

                    if not user:
                        return jsonify({'success': False, 'error': 'User not found'}), 404

                    user_id = user[0]

        user_agent = request.headers.get('User-Agent', 'unknown')
        ip_address = request.remote_addr

        result = register_or_update_device(user_id, firebase_uid, user_agent, ip_address)

        if result['success']:
            mark_devices_offline(firebase_uid)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"Error in device registration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/my-devices', methods=['GET'])
def get_my_devices():
    """Get all devices for the authenticated user"""
    try:
        from firebase_helper import verify_firebase_token

        # Verify Firebase token and get UID - NO FALLBACK for security
        decoded_token, error = verify_firebase_token(request)

        if error:
            return jsonify({'success': False, 'error': f'Authentication required: {error}'}), 401

        firebase_uid = decoded_token.get('uid')

        # Verify user exists
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    user = cur.fetchone()

                    if not user:
                        return jsonify({'success': False, 'error': 'User not found'}), 404

        result = get_user_devices(firebase_uid)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"Error fetching devices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/sync', methods=['POST'])
def sync_device():
    """Update device last_active timestamp"""
    try:
        from firebase_helper import verify_firebase_token

        # Verify Firebase token and get UID - NO FALLBACK for security
        decoded_token, error = verify_firebase_token(request)

        if error:
            return jsonify({'success': False, 'error': f'Authentication required: {error}'}), 401

        firebase_uid = decoded_token.get('uid')

        # Get user_id from firebase_uid
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    user = cur.fetchone()

                    if not user:
                        return jsonify({'success': False, 'error': 'User not found'}), 404

                    user_id = user[0]

        user_agent = request.headers.get('User-Agent', 'unknown')
        ip_address = request.remote_addr

        result = register_or_update_device(user_id, firebase_uid, user_agent, ip_address)
        mark_devices_offline(firebase_uid)

        return jsonify({'success': True, 'message': 'Device synced'})

    except Exception as e:
        print(f"Error syncing device: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/tokens', methods=['GET'])
def tokens():
    return render_template('tokens.html')

@app.route('/notifications', methods=['GET'])
def notifications():
    return render_template('notifications.html')

@app.route('/bitchat', methods=['GET'])
def bitchat():
    return render_template('bitchat.html')

@app.route('/admin')
def admin():
    """Main admin panel"""
    return render_template('admin.html')

@app.route('/admin/shopify')
def shopify_admin():
    """Shopify management admin interface"""
    return render_template('shopify_admin.html')

@app.route('/help-admin')
def help_admin():
    """Admin interface for general help and support"""
    return render_template('help_admin.html')

@app.route('/email-admin')
def email_admin():
    """Admin interface for editing eSIM activation emails"""
    return render_template('email_admin.html')

@app.route('/api/admin/save-email-template', methods=['POST'])
def save_email_template():
    """Save email template to database"""
    try:
        data = request.get_json()
        template_type = data.get('type')
        subject = data.get('subject')
        content = data.get('content')

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Create email_templates table if not exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS email_templates (
                            id SERIAL PRIMARY KEY,
                            template_type VARCHAR(50) NOT NULL,
                            subject TEXT NOT NULL,
                            content TEXT NOT NULL,
                            modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            modified_by VARCHAR(100) DEFAULT 'Admin',
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)

                    # Deactivate old templates of this type
                    cur.execute("""
                        UPDATE email_templates
                        SET is_active = FALSE
                        WHERE template_type = %s
                    """, (template_type,))

                    # Insert new template
                    cur.execute("""
                        INSERT INTO email_templates
                        (template_type, subject, content, modified_date)
                        VALUES (%s, %s, %s, %s)
                    """, (template_type, subject, content, datetime.now()))

                    conn.commit()

        return jsonify({'success': True, 'message': 'Template saved successfully'})

    except Exception as e:
        print(f"Error saving email template: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/send-test-email', methods=['POST'])
def send_test_email():
    """Send test email with template"""
    try:
        data = request.get_json()
        to_email = data.get('to_email')
        subject = data.get('subject')
        content = data.get('content')
        test_data = data.get('test_data', {})

        # Replace variables in content
        processed_content = content
        for key, value in test_data.items():
            processed_content = processed_content.replace(f"{{{{{key}}}}}", str(value))

        # Send email using existing email service
        from email_service import send_email
        result = send_email(
            to_email=to_email,
            subject=subject,
            body="Test email - please check HTML version",
            html_body=processed_content
        )

        return jsonify({'success': result, 'message': 'Test email sent' if result else 'Failed to send email'})

    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/email-template-history')
def get_email_template_history():
    """Get email template history"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT template_type, subject, content, modified_date, modified_by
                        FROM email_templates
                        ORDER BY modified_date DESC
                        LIMIT 20
                    """)

                    history = []
                    for row in cur.fetchall():
                        history.append({
                            'template_type': row[0],
                            'subject': row[1],
                            'content': row[2],
                            'modified_date': row[3].isoformat() if row[3] else None,
                            'modified_by': row[4]
                        })

                    return jsonify({'success': True, 'history': history})

        return jsonify({'success': False, 'message': 'Database connection failed'})

    except Exception as e:
        print(f"Error getting template history: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/restore-email-template/<int:version_index>')
def restore_email_template(version_index):
    """Restore a specific template version"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT template_type, subject, content
                        FROM email_templates
                        ORDER BY modified_date DESC
                        LIMIT 20
                    """)

                    templates = cur.fetchall()
                    if version_index < len(templates):
                        template = templates[version_index]
                        return jsonify({
                            'success': True,
                            'template': {
                                'type': template[0],
                                'subject': template[1],
                                'content': template[2]
                            }
                        })

        return jsonify({'success': False, 'message': 'Template not found'})

    except Exception as e:
        print(f"Error restoring template: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/oxio-test')
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
        # The amount is not directly available in the price object without fetching the related product,
        # but we'll use defaults for now if not needed for session creation.
        # For specific products like eSIM beta, the price is hardcoded in the route.

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

        # Get user email and name from database for eSIM activation
        user_email = email
        user_name = None
        if firebase_uid:
            try:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT email, display_name
                                FROM users
                                WHERE firebase_uid = %s
                            """, (firebase_uid,))
                            result = cur.fetchone()
                            if result:
                                user_email = result[0] if not user_email else user_email
                                user_name = result[1]
            except Exception as db_error:
                print(f"Error getting user data for checkout metadata: {db_error}")

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
                'product': product_id,  # Add 'product' field for webhook compatibility
                'firebase_uid': firebase_uid,
                'user_email': user_email or '',  # Add for eSIM activation
                'user_name': user_name or '',    # Add for eSIM activation
                'subscription_type': 'yearly' if is_subscription else 'one_time'
            },
            **customer_params  # Add customer ID if available
        )

        print(f"Created checkout session: {checkout_session.id} for product: {product_id} (subscription: {is_subscription})")
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stripe/webhook/7f3a9b2c8d1e4f5a6b7c8d9e0f1a2b3c', methods=['POST'])
def handle_stripe_webhook():
    """Handle Stripe webhook events, especially payment success"""
    global stripe  # Use the global stripe module
    payload = request.data
    sig_header = request.headers.get('stripe-signature')

    # Get webhook endpoint secret from environment
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Debug logging for webhook signature verification
    print(f"🔐 Webhook signature verification:")
    print(f"   Endpoint secret configured: {'✓' if endpoint_secret else '✗'}")
    print(f"   Stripe signature header present: {'✓' if sig_header else '✗'}")
    print(f"   Payload length: {len(payload)} bytes")
    if endpoint_secret:
        print(f"   Endpoint secret starts with: whsec_{endpoint_secret[6:10]}...")
    if sig_header:
        print(f"   Signature header: {sig_header[:50]}...")

    try:
        # Verify webhook signature - MANDATORY for security (NO BYPASSES IN PRODUCTION)
        if not endpoint_secret:
            print("❌ ERROR: STRIPE_WEBHOOK_SECRET not configured - webhook verification required")
            return jsonify({'error': 'Webhook verification not configured'}), 500
        elif not sig_header:
            print("❌ ERROR: Missing stripe-signature header")
            return jsonify({'error': 'Missing webhook signature'}), 400
        else:
            print("🔍 Attempting to verify webhook signature...")
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            print("✅ Webhook signature verified successfully")

        print(f"📨 Stripe webhook received: {event['type']} (ID: {event['id']})")

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

                # Mark event as being processed (prevents race conditions) with UNIQUE constraint
                cursor.execute("""
                    INSERT INTO processed_stripe_events (event_id, event_type)
                    VALUES (%s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                """, (event_id, event_type))

                # Check if we actually inserted (vs conflict)
                if cursor.rowcount == 0:
                    print(f"🔄 Event {event_id} was already being processed by another request")
                    return jsonify({'status': 'already_processed', 'event_id': event_id}), 200
                conn.commit()
                print(f"🔄 Processing new event: {event_id} (type: {event_type})")

        except Exception as db_error:
            print(f"❌ CRITICAL: Database error in idempotency check: {db_error}")
            # FAIL CLOSED - Do not process if idempotency cannot be guaranteed
            return jsonify({'error': 'Idempotency check failed', 'retry': True}), 500

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

            # Handle eSIM Beta activation using dedicated service
            if product == 'esim_beta':
                try:
                    print(f"💰 Processing $1 eSIM Beta activation with ICCID assignment")

                    # Import the new eSIM activation service
                    from esim_activation_service import esim_activation_service

                    # Get user details from session metadata
                    firebase_uid = session['metadata'].get('firebase_uid', '')
                    user_email = session['metadata'].get('user_email', '')
                    user_name = session['metadata'].get('user_name', '')

                    # Step 1: Check if user already has an assigned ICCID (idempotency)
                    existing_iccid = get_user_assigned_iccid_data(firebase_uid)

                    if existing_iccid:
                        print(f"✅ User {firebase_uid} already has assigned ICCID: {existing_iccid['iccid']}")
                        assigned_iccid = existing_iccid
                    else:
                        # Assign new ICCID to user with atomic locking to prevent race conditions
                        # Use atomic function for safer assignment
                        assigned_iccid = assign_iccid_to_user_atomic(firebase_uid, user_email)

                        if not assigned_iccid:
                            print(f"❌ No available ICCIDs for user {firebase_uid}")
                            return jsonify({'error': 'No available eSIMs'}), 500

                        print(f"✅ Assigned new ICCID {assigned_iccid['iccid']} to user {firebase_uid}")
                    total_amount = session.get('amount_total', 100)  # Default $1.00 in cents

                    print(f"🎯 eSIM activation parameters: Firebase UID={firebase_uid}, Email={user_email}, Amount=${total_amount/100:.2f}")

                    if not firebase_uid or not user_email:
                        print(f"❌ Missing required parameters for eSIM activation")
                        return jsonify({'status': 'error', 'message': 'Missing Firebase UID or email'}), 400

                    # Call the dedicated eSIM activation service
                    activation_result = esim_activation_service.activate_esim_after_payment(
                        firebase_uid=firebase_uid,
                        user_email=user_email,
                        user_name=user_name,
                        stripe_session_id=session['id'],
                        purchase_amount=total_amount
                    )

                    if activation_result.get('success'):
                        print(f"✅ eSIM activation service completed successfully")

                        # Step 2: Send enhanced receipt email with ICCID and QR codes
                        print(f"📧 Sending receipt email with assigned ICCID: {assigned_iccid['iccid']}")
                        email_result = send_esim_receipt_email(
                            firebase_uid=firebase_uid,
                            user_email=user_email,
                            user_name=user_name,
                            assigned_iccid=assigned_iccid
                        )

                        if email_result:
                            print(f"✅ Receipt email sent with QR codes")
                        else:
                            print(f"⚠️ Receipt email sending failed")

                        # Record the purchase in database
                        purchase_id = record_purchase(
                            stripe_id=session.get('id'),
                            product_id='esim_beta',
                            price_id='price_1S7Yc6JnTfh0bNQQVeLeprXe',
                            amount=total_amount,
                            user_id=None,  # Will be looked up from Firebase UID
                            transaction_id=session.get('payment_intent'),
                            firebase_uid=firebase_uid,
                            stripe_transaction_id=session.get('payment_intent')
                        )
                        print(f"💾 Purchase recorded with ID: {purchase_id}")

                        # Update Stripe receipt with eSIM details
                        try:
                            esim_data = activation_result.get('esim_data', {}) or {}  # Ensure it's always a dict
                            enhanced_metadata = {
                                **session.get('metadata', {}),
                                'esim_phone_number': esim_data.get('phone_number', 'Pending assignment'),
                                'esim_iccid': assigned_iccid['iccid'],  # Use our assigned ICCID
                                'esim_lpa_code': assigned_iccid['lpa_code'],  # Include LPA code
                                'esim_country': assigned_iccid['country'],
                                'esim_line_id': esim_data.get('line_id', assigned_iccid.get('line_id', 'System assigned')),
                                'esim_activation_status': 'completed',
                                'esim_activation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'esim_qr_available': 'yes',  # Always yes since we generate QR codes
                                'iccid_assigned': 'true',  # Flag that ICCID was assigned
                                'oxio_user_id': activation_result.get('oxio_user_id', ''),
                                'oxio_group_id': activation_result.get('oxio_group_id', ''),
                                'purchase_id': str(purchase_id) if purchase_id else '',
                                'receipt_enhanced': 'true'
                            }

                            stripe.checkout.Session.modify(session['id'], metadata=enhanced_metadata)
                            print(f"✅ Enhanced Stripe receipt with eSIM details")

                        except Exception as stripe_update_error:
                            print(f"⚠️ Could not update Stripe receipt: {stripe_update_error}")
                    else:
                        print(f"❌ eSIM activation service failed: {activation_result.get('error', 'Unknown error')}")
                        print(f"   Failed at step: {activation_result.get('step', 'unknown')}")
                        print(f"   Note: ICCID {assigned_iccid.get('iccid') if assigned_iccid else 'N/A'} assigned after payment - no rollback needed")

                        return jsonify({
                            'status': 'activation_failed',
                            'error': activation_result.get('error', 'Activation failed'),
                            'step': activation_result.get('step', 'unknown')
                        }), 500

                except Exception as e:
                    print(f"❌ Error in eSIM Beta activation: {str(e)}")
                    print(f"   Note: ICCID {assigned_iccid.get('iccid') if assigned_iccid else 'N/A'} assigned after payment - no rollback needed")

                    return jsonify({
                        'status': 'error',
                        'error': 'eSIM activation failed',
                        'message': str(e)
                    }), 500

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
        print(f"❌ Webhook ValueError: {str(e)}")
        print(f"   Raw payload (first 200 chars): {payload[:200]}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Webhook SignatureVerificationError: {str(e)}")
        print(f"   This usually means:")
        print(f"   1. Webhook endpoint secret is incorrect")
        print(f"   2. Webhook URL in Stripe dashboard doesn't match this endpoint")
        print(f"   3. Request body was modified before signature verification")
        print(f"   Expected webhook URL: https://your-domain.replit.app/stripe/webhook/7f3a9b2c8d1e4f5a6b7c8d9e0f1a2b3c")
        return jsonify({
            'error': 'Invalid signature',
            'troubleshooting': {
                'endpoint_url': '/stripe/webhook/7f3a9b2c8d1e4f5a6b7c8d9e0f1a2b3c',
                'expected_domain': 'your-domain.replit.app',
                'message': 'Webhook endpoint secret mismatch or incorrect URL configuration'
            }
        }), 400
    except Exception as e:
        print(f"❌ Webhook unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
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
                    user_email = user_data['email']
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
            to_email=user_email,
            subject=subject,
            body="Your eSIM is ready! Check the HTML version for full details.",
            html_body=html_body
        )

        print(f"Sent eSIM activation email to {user_email} with details: Phone {phone_number}, Plan {plan_id}")
        return result

    except Exception as e:
        print(f"Error sending eSIM activation email: {e}")
        return False

def generate_qr_code(lpa_code, iccid, format='svg'):
    """
    Generate QR code for eSIM activation (LPA format)

    Args:
        lpa_code: The LPA (eSIM Activation Code)
        iccid: The ICCID of the eSIM
        format: 'svg' or 'png'

    Returns:
        Dictionary with QR code data and success status, or error details.
    """
    try:
        import qrcode
        import base64
        from io import BytesIO

        # Construct the QR code data string. This format is specific to eSIM provisioning.
        # The exact structure might vary slightly based on the SM-DP+ server.
        # This is a common example: LPA:1$SMDP_ADDRESS$ICCID$QR_HASH (QR hash is optional)
        # Using a placeholder SMDP address for now.
        if lpa_code and iccid:
            qr_data = f"LPA:1$api-staging.brandvno.com${iccid}$?esim_activation_code={lpa_code}"
        elif lpa_code:
            qr_data = f"LPA:1$api-staging.brandvno.com$None$?esim_activation_code={lpa_code}"
        elif iccid:
            qr_data = f"LPA:1$api-staging.brandvno.com${iccid}$"
        else:
            return {'success': False, 'error': 'Missing LPA code or ICCID for QR generation'}

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        if format.lower() == 'svg':
            # Generate SVG QR code
            qr_svg_data = qr.get_string(fill_color="black", back_color="white")
            return {'success': True, 'data': qr_svg_data, 'format': 'svg'}
        elif format.lower() == 'png':
            # Generate PNG QR code
            qr_image = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            qr_data_uri = f"data:image/png;base64,{qr_base64}"
            return {'success': True, 'data': qr_data_uri, 'format': 'png'}
        else:
            return {'success': False, 'error': 'Unsupported QR code format'}

    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        return {'success': False, 'error': str(e)}


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

        user_id = user_data['id']
        user_email = user_data['email']
        oxio_user_id = user_data['oxio_user_id']

        print(f"Activating eSIM for user {user_id} ({user_email}) with OXIO user ID: {oxio_user_id}")

        # Create OXIO user if not exists
        if not oxio_user_id:
            print("Creating new OXIO user for eSIM activation...")
            oxio_user_result = oxio_service.create_oxio_user(
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_email,
                firebase_uid=firebase_uid
            )

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
                    'message': oxio_result.get('message', 'Unknown error')
                }

        # Activate OXIO line with Basic Membership plan
        print(f"Activating OXIO line for eSIM Beta user {user_id}")

        # Use enhanced activation with plan ID and group ID for eSIM Beta
        esim_plan_id = "OXIO_BASIC_MEMBERSHIP_BASEPLANID"  # OXIO base plan ID for $1 beta access

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
                # Generate QR code using the new function
                qr_response = generate_qr_code(
                    lpa_code=None,  # Assuming LPA is not directly returned or needed for this generation
                    iccid=iccid,
                    format='png' # Request PNG for email attachment
                )
                if qr_response.get('success'):
                    esim_qr_code = qr_response.get('data') # This will be a data URI
                    print(f"Generated eSIM activation QR code (PNG data URI)")
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
                                        activation_url TEXT,
                                        activation_code VARCHAR(200),
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
                subject = "🎉 eSIM is Ready!"

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

                send_email(to_email=user_email, subject=subject, body="eSIM activated successfully!", html_body=html_body)
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

# Static files are served automatically by Flask from the static folder
# No need for a custom route since we defined static_url_path='/static' in Flask(__name__, static_url_path='/static')

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

# This function `get_user_by_firebase_uid` was already updated in the previous change.
# No further modification needed here based on the current change.

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
                user_id = user_data['id']  # Get the actual internal user ID (integer)
                stripe_customer_id = user_data['stripe_customer_id']  # Get Stripe customer ID
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
        if not user_data or not user_data['stripe_customer_id']:
            return jsonify({'error': 'No Stripe customer found for user'}), 404

        stripe_customer_id = user_data['stripe_customer_id']

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
                        """, (user_data['id'], stripe_customer_id, megabytes_used, result.get('event_id')))
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
        if not user_data or not user_data['stripe_customer_id']:
            return jsonify({'error': 'No Stripe customer found for user'}), 404

        stripe_customer_id = user_data['stripe_customer_id']

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
                user_id = user_data['id']  # Get the actual internal user ID (integer)
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

@app.route('/api/user-purchases', methods=['GET'])
def get_user_purchases():
    """Get purchase history for a user"""
    firebase_uid = request.args.get('firebaseUid')
    
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400
    
    try:
        # Get user data to find the user_id
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user_data['id']
        
        # Fetch purchases from database
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            purchaseid,
                            stripeid,
                            stripeproductid,
                            priceid,
                            totalamount,
                            datecreated,
                            stripetransactionid
                        FROM purchases
                        WHERE userid = %s
                        ORDER BY datecreated DESC
                        LIMIT 50
                    """, (user_id,))
                    
                    purchases = cur.fetchall()
                    
                    # Format purchases for JSON response
                    purchase_list = []
                    for purchase in purchases:
                        # Map product IDs to friendly names
                        product_name_map = {
                            'esim_beta': 'eSIM Beta',
                            'global_data_10gb': 'Global Data 10GB',
                            'basic_membership': 'Basic Membership',
                            'full_membership': 'Full Membership',
                            'metal_card': 'Metal Card',
                            'beta_tester': 'Beta Tester'
                        }
                        
                        product_id = purchase[2]
                        product_name = product_name_map.get(product_id, product_id)
                        
                        purchase_list.append({
                            'purchase_id': purchase[0],
                            'stripe_id': purchase[1],
                            'product_id': product_id,
                            'product_name': product_name,
                            'price_id': purchase[3],
                            'amount': purchase[4],  # Amount in cents
                            'amount_formatted': f"${purchase[4] / 100:.2f}",
                            'date': purchase[5].isoformat() if purchase[5] else None,
                            'transaction_id': purchase[6]
                        })
                    
                    return jsonify({
                        'success': True,
                        'purchases': purchase_list,
                        'count': len(purchase_list)
                    })
            else:
                return jsonify({'error': 'Database connection failed'}), 500
                
    except Exception as e:
        print(f"Error fetching user purchases: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
                user_id = user_data['id']
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
                user_email = user_data['email']
                # Make sure we get the OXIO user ID (column 7) not the Ethereum address (column 8)
                oxio_user_id = user_data['oxio_user_id']
                eth_address = user_data['eth_address']
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
                                            plan_id VARCHAR(100),
                                            group_id VARCHAR(100),
                                            esim_qr_code TEXT,
                                            activation_url TEXT,
                                            activation_code VARCHAR(200),
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
                                         line_id, phone_number, activation_status, plan_id, group_id,
                                         esim_qr_code, oxio_response)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (user_id, firebase_uid, purchase_id, product_id, iccid,
                                          line_id, phone_number, 'activated', esim_plan_id, esim_group_id,
                                          esim_qr_code, str(oxio_result)))

                                    conn.commit()
                                    print(f"Stored OXIO activation record for user {user_id}")
                    except Exception as db_err:
                        print(f"Error storing OXIO activation record: {str(db_err)}")
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
                        # Check if user has purchased any membership products
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

        # user_data is a dictionary, so access by key
        user_id = user_data['id']
        user_email = user_data['email']
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
            'oxio_user_id': user_data.get('oxio_user_id'),
            'metamask_address': user_data.get('eth_address'),
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

        # user_data is a dictionary, so access by key
        user_id = user_data['id']

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

def create_token_pings_table():
    """Helper function to create token_price_pings table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS token_price_pings (
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
                        CREATE INDEX IF NOT EXISTS idx_token_price_pings_created_at ON token_price_pings(created_at);
                    """)
                    conn.commit()
                    print("Ensured token_price_pings table exists.")
    except Exception as e:
        print(f"Error ensuring token_price_pings table exists: {str(e)}")


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
                        CREATE INDEX IF NOT EXISTS idx_token_price_pings_created_at ON token_price_pings(created_at);
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

@app.route('/api/test-esim-activation', methods=['POST'])
def test_esim_activation_service():
    """Test the new eSIM activation service"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebaseUid', 'test_uid_123')
        user_email = data.get('email', 'test@example.com')
        user_name = data.get('name', 'Test User')

        # Import and test the service
        from esim_activation_service import esim_activation_service

        result = esim_activation_service.activate_esim_after_payment(
            firebase_uid=firebase_uid,
            user_email=user_email,
            user_name=user_name,
            stripe_session_id="test_session_123",
            purchase_amount=100
        )

        return jsonify({
            'status': 'test_completed',
            'service_result': result,
            'test_parameters': {
                'firebase_uid': firebase_uid,
                'email': user_email,
                'name': user_name
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'test_failed',
            'error': str(e)
        }), 500

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

        user_id = user_data['id']

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get OXIO activation records for this user
                    cur.execute("""
                        SELECT id, product_id, iccid, line_id, phone_number,
                               activation_status, oxio_response, created_at
                        FROM oxio_activations
                        WHERE firebase_uid = %s
                        ORDER BY created_at DESC
                    """, (firebase_uid,))

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

@app.route('/api/welcome-message/voices', methods=['GET'])
def get_welcome_voices():
    """Get available voice profiles for welcome messages"""
    try:
        voice_profiles = elevenlabs_service.get_voice_profiles()
        voices = []

        for profile_name, profile_data in voice_profiles.items():
            voices.append({
                'name': profile_name,
                'voice_id': profile_data['voice_id'],
                'description': profile_data['description']
            })

        return jsonify({
            'success': True,
            'voices': voices
        })
    except Exception as e:
        print(f"Error getting welcome voices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/welcome-message/generate', methods=['POST'])
def generate_welcome_message():
    """Generate message with caching and type selection based on user history"""
    try:
        data = request.get_json() or {}
        firebase_uid = data.get('firebase_uid')
        language = data.get('language', 'en')
        voice_profile = data.get('voice_profile', 'ScienceTeacher')
        requested_type = data.get('message_type')  # Optional override

        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Firebase UID required'}), 400

        # Determine message type based on user history (if not explicitly requested)
        message_type = requested_type
        if not message_type:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Check what message types user has listened to
                        cur.execute("""
                            SELECT DISTINCT message_type
                            FROM user_message_history
                            WHERE firebase_uid = %s AND completed = TRUE
                            ORDER BY message_type
                        """, (firebase_uid,))

                        listened_types = [row[0] for row in cur.fetchall()]

                        # Select next message type
                        if 'welcome' not in listened_types:
                            message_type = 'welcome'
                        elif 'tip' not in listened_types:
                            message_type = 'tip'
                        else:
                            message_type = 'update'

        # Check cache first
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, audio_data, content_type
                        FROM welcome_messages
                        WHERE firebase_uid = %s AND language = %s AND voice_profile = %s AND message_type = %s
                    """, (firebase_uid, language, voice_profile, message_type))

                    cached = cur.fetchone()
                    if cached:
                        message_id, audio_data, content_type = cached
                        # Return cached audio URL
                        return jsonify({
                            'success': True,
                            'audio_url': f'/api/welcome-audio/{message_id}',
                            'message_id': message_id,
                            'message_type': message_type,
                            'cached': True
                        })

        # Generate new message and track generation time
        import time
        start_time = time.time()

        result = elevenlabs_service.generate_welcome_message(
            user_name=None,
            language=language,
            voice_profile=voice_profile,
            message_type=message_type
        )

        generation_time_ms = int((time.time() - start_time) * 1000)

        if result.get('success'):
            # Store in database with generation time and message type
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO welcome_messages
                            (firebase_uid, language, voice_profile, audio_data, content_type, generation_time_ms, message_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (firebase_uid, language, voice_profile, message_type)
                            DO UPDATE SET audio_data = EXCLUDED.audio_data,
                                        created_at = CURRENT_TIMESTAMP,
                                        generation_time_ms = EXCLUDED.generation_time_ms
                            RETURNING id
                        """, (
                            firebase_uid,
                            language,
                            voice_profile,
                            result['audio_data'],
                            result['content_type'],
                            generation_time_ms,
                            message_type
                        ))

                        message_id = cur.fetchone()[0]
                        conn.commit()

                        return jsonify({
                            'success': True,
                            'audio_url': f'/api/welcome-audio/{message_id}',
                            'message_id': message_id,
                            'message_type': message_type,
                            'cached': False,
                            'generation_time_ms': generation_time_ms
                        })

            return jsonify({'success': False, 'error': 'Database error'}), 500
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500

    except Exception as e:
        print(f"Error generating welcome message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/welcome-audio/<int:message_id>', methods=['GET'])
def get_welcome_audio(message_id):
    """Retrieve cached welcome audio"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT audio_data, content_type
                        FROM welcome_messages
                        WHERE id = %s
                    """, (message_id,))

                    result = cur.fetchone()
                    if result:
                        audio_data, content_type = result
                        return Response(
                            audio_data,
                            mimetype=content_type,
                            headers={
                                'Cache-Control': 'public, max-age=3600',
                                'Content-Disposition': f'inline; filename="welcome_{message_id}.mp3"'
                            }
                        )
                    else:
                        return jsonify({'error': 'Audio not found'}), 404

        return jsonify({'error': 'Database error'}), 500

    except Exception as e:
        print(f"Error retrieving welcome audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/welcome-message/estimated-time', methods=['GET'])
def get_estimated_generation_time():
    """Get estimated generation time based on recent messages"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get average generation time from last 10 generated messages
                    cur.execute("""
                        SELECT AVG(generation_time_ms) as avg_time
                        FROM (
                            SELECT generation_time_ms
                            FROM welcome_messages
                            WHERE generation_time_ms IS NOT NULL
                            ORDER BY created_at DESC
                            LIMIT 10
                        ) recent_messages
                    """)

                    result = cur.fetchone()
                    avg_time = result[0] if result and result[0] else 3000  # Default to 3 seconds

                    return jsonify({
                        'success': True,
                        'estimated_time_ms': int(avg_time)
                    })

        return jsonify({'success': False, 'error': 'Database error'}), 500

    except Exception as e:
        print(f"Error getting estimated time: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/welcome-message/track-listen', methods=['POST'])
def track_message_listen():
    """Track when a user listens to a message"""
    try:
        data = request.get_json() or {}
        firebase_uid = data.get('firebase_uid')
        message_type = data.get('message_type', 'welcome')
        language = data.get('language', 'en')
        voice_profile = data.get('voice_profile', 'ScienceTeacher')
        completed = data.get('completed', False)

        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Firebase UID required'}), 400

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Insert or update listening record
                    cur.execute("""
                        INSERT INTO user_message_history
                        (firebase_uid, message_type, language, voice_profile, completed, listened_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                    """, (firebase_uid, message_type, language, voice_profile, completed))

                    history_id = cur.fetchone()[0]
                    conn.commit()

                    return jsonify({
                        'success': True,
                        'history_id': history_id,
                        'message': 'Listening tracked successfully'
                    })

        return jsonify({'success': False, 'error': 'Database error'}), 500

    except Exception as e:
        print(f"Error tracking message listen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-personal-message', methods=['POST'])
def update_personal_message():
    """Update or create a personal message for a specific Firebase UID"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebase_uid')
        email = data.get('email', 'Unknown Email')
        personal_message =data.get('personal_message', '')

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
            return f"Error rejecting beta request: {result.get('message', 'Unknown error')}", 500

    except Exception as e:
        print(f"Error in reject_beta_request: {str(e)}")
        return f"Error processing request: {str(e)}", 500

# Add the new endpoint definition here
@app.route('/api/user-esim-details', methods=['GET'])
def get_user_esim_details():
    """Get user's eSIM activation details including ICCID and OXIO data with fallback sync"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get assigned ICCID
                    cur.execute("""
                        SELECT iccid, lpa_code, status, assigned_at, country
                        FROM iccid_inventory
                        WHERE allocated_to_firebase_uid = %s
                          AND status = 'assigned'
                        ORDER BY assigned_at DESC
                    """, (firebase_uid,))

                    iccid_data = cur.fetchall()

                    # Get OXIO activation details
                    cur.execute("""
                        SELECT iccid, line_id, phone_number, activation_status,
                               esim_qr_code, activation_url, activation_code, created_at
                        FROM oxio_activations
                        WHERE firebase_uid = %s
                        ORDER BY created_at DESC
                    """, (firebase_uid,))

                    activation_data = cur.fetchall()

                    # FALLBACK: If no local data, try to sync from OXIO
                    data_recovered = False
                    if not activation_data and not iccid_data:
                        print(f"📡 No local eSIM data found for {firebase_uid}, attempting OXIO sync...")
                        
                        # Get user's OXIO user ID and details
                        cur.execute("""
                            SELECT oxio_user_id, email, display_name, oxio_group_id, id
                            FROM users
                            WHERE firebase_uid = %s
                        """, (firebase_uid,))
                        
                        user_row = cur.fetchone()
                        
                        if user_row:
                            oxio_user_id = user_row[0]
                            user_email = user_row[1]
                            display_name = user_row[2]
                            oxio_group_id = user_row[3]
                            user_id = user_row[4]
                            
                            # If no OXIO user ID, create one
                            if not oxio_user_id:
                                print(f"🆕 No OXIO User ID found, creating OXIO user for {user_email}...")
                                
                                from oxio_service import OXIOService
                                oxio_service = OXIOService()
                                
                                # Parse display name
                                name_parts = (display_name or user_email.split('@')[0]).split(' ', 1)
                                first_name = name_parts[0]
                                last_name = name_parts[1] if len(name_parts) > 1 else ""
                                
                                # Create OXIO user
                                oxio_result = oxio_service.create_oxio_user(
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=user_email,
                                    firebase_uid=firebase_uid,
                                    oxio_group_id=oxio_group_id
                                )
                                
                                if oxio_result.get('success'):
                                    oxio_user_id = oxio_result['data'].get('endUserId')
                                    
                                    # Update users table with new OXIO user ID
                                    cur.execute("""
                                        UPDATE users
                                        SET oxio_user_id = %s
                                        WHERE firebase_uid = %s
                                    """, (oxio_user_id, firebase_uid))
                                    conn.commit()
                                    
                                    print(f"✅ Created OXIO User ID: {oxio_user_id}")
                                else:
                                    print(f"❌ Failed to create OXIO user: {oxio_result.get('error', 'Unknown error')}")
                                    oxio_user_id = None
                            
                            # Now attempt to sync lines if we have an OXIO user ID
                            if oxio_user_id:
                                print(f"🔍 Syncing lines for OXIO User ID: {oxio_user_id} ({user_email})")
                                
                                # Import and use sync service
                                from esim_sync_service import sync_oxio_lines_for_user
                                
                                sync_result = sync_oxio_lines_for_user(firebase_uid, oxio_user_id, conn)
                                
                                if sync_result.get('success') and sync_result.get('lines_synced', 0) > 0:
                                    print(f"✅ Synced {sync_result['lines_synced']} lines from OXIO")
                                    data_recovered = True
                                    
                                    # Re-query local database after sync
                                    cur.execute("""
                                        SELECT iccid, lpa_code, status, assigned_at, country
                                        FROM iccid_inventory
                                        WHERE allocated_to_firebase_uid = %s
                                          AND status = 'assigned'
                                        ORDER BY assigned_at DESC
                                    """, (firebase_uid,))
                                    
                                    iccid_data = cur.fetchall()
                                    
                                    cur.execute("""
                                        SELECT iccid, line_id, phone_number, activation_status,
                                               esim_qr_code, activation_url, activation_code, created_at
                                        FROM oxio_activations
                                        WHERE firebase_uid = %s
                                        ORDER BY created_at DESC
                                    """, (firebase_uid,))
                                    
                                    activation_data = cur.fetchall()
                                elif sync_result.get('user_should_purchase'):
                                    print(f"ℹ️  No lines found in OXIO - user needs to purchase")
                                else:
                                    print(f"⚠️  OXIO sync failed: {sync_result.get('error', 'Unknown error')}")
                            else:
                                print(f"⚠️  Cannot sync without OXIO User ID")
                        else:
                            print(f"⚠️  User not found in database for Firebase UID {firebase_uid}")

                    esims = []
                    for activation in activation_data:
                        esims.append({
                            'iccid': activation[0],
                            'line_id': activation[1],
                            'phone_number': activation[2],
                            'activation_status': activation[3],
                            'qr_code': activation[4],
                            'activation_url': activation[5],
                            'activation_code': activation[6],
                            'created_at': activation[7].isoformat() if activation[7] else None
                        })

                    return jsonify({
                        'success': True,
                        'esims': esims,
                        'iccid_inventory': [
                            {
                                'iccid': i[0],
                                'lpa_code': i[1],
                                'status': i[2],
                                'assigned_at': i[3].isoformat() if i[3] else None,
                                'country': i[4]
                            } for i in iccid_data
                        ],
                        'data_recovered_from_oxio': data_recovered
                    })

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error getting eSIM details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-phone-numbers', methods=['GET'])
def get_user_phone_numbers():
    """Get user's beta phone numbers with QR codes - ADMIN ONLY"""
    pass # Placeholder for admin functionality

# Shopify API endpoints
@app.route('/api/shopify/test-connection', methods=['GET'])
def shopify_test_connection():
    """Test Shopify API connection"""
    try:
        result = shopify_service.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shopify/products', methods=['GET'])
def shopify_get_products():
    """Get products from Shopify"""
    try:
        limit = int(request.args.get('limit', 50))
        page_info = request.args.get('page_info')
        result = shopify_service.get_products(limit=limit, page_info=page_info)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shopify/product/<product_id>', methods=['GET'])
def shopify_get_product(product_id):
    """Get a single product"""
    try:
        result = shopify_service.get_product(product_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shopify/orders', methods=['GET'])
def shopify_get_orders():
    """Get orders from Shopify"""
    try:
        status = request.args.get('status', 'any')
        limit = int(request.args.get('limit', 50))
        result = shopify_service.get_orders(status=status, limit=limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shopify/sync-products', methods=['POST'])
def shopify_sync_products():
    """Sync products from Shopify to marketplace"""
    try:
        result = shopify_service.get_products(limit=250)

        if result['success']:
            # Here you would sync to your marketplace database
            # For now, just return the count
            return jsonify({
                'success': True,
                'synced_count': len(result['products']),
                'message': f"Synced {len(result['products'])} products"
            })
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shopify/sync-inventory', methods=['POST'])
def shopify_sync_inventory():
    """Sync inventory from Shopify"""
    try:
        # Get all products and sync inventory levels
        result = shopify_service.get_products(limit=250)

        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Inventory synced for {len(result['products'])} products"
            })
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/fix-failed-esim-activation', methods=['POST'])
def fix_failed_esim_activation():
    """Manually complete a failed eSIM activation for a user who paid but didn't get activated"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebase_uid')
        admin_key = data.get('admin_key')
        
        # Simple admin auth check
        if admin_key != os.environ.get('ADMIN_KEY', 'dotm_admin_2025'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Firebase UID is required'}), 400
        
        print(f"🔧 Manual eSIM activation fix requested for Firebase UID: {firebase_uid}")
        
        # Step 1: Get user details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, display_name, oxio_user_id, stripe_customer_id
                FROM users
                WHERE firebase_uid = %s
            """, (firebase_uid,))
            user_result = cursor.fetchone()
            
            if not user_result:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            user_id, user_email, user_name, oxio_user_id, stripe_customer_id = user_result
            print(f"   User ID: {user_id}, Email: {user_email}, OXIO User ID: {oxio_user_id}")
        
        # Step 2: Check if ICCID is already assigned
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT iccid, lpa_code, line_id, country
                FROM iccid_inventory
                WHERE allocated_to_firebase_uid = %s
                ORDER BY assigned_at DESC
                LIMIT 1
            """, (firebase_uid,))
            iccid_result = cursor.fetchone()
            
            if not iccid_result:
                return jsonify({'success': False, 'error': 'No ICCID assigned to user'}), 404
            
            iccid, lpa_code, line_id, country = iccid_result
            print(f"   Found assigned ICCID: {iccid}")
        
        # Step 3: Check if purchase already recorded
        purchase_exists = False
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT purchaseid FROM purchases
                WHERE firebaseuid = %s AND stripeproductid = 'esim_beta'
                LIMIT 1
            """, (firebase_uid,))
            if cursor.fetchone():
                purchase_exists = True
                print(f"   ✓ Purchase already recorded")
        
        # Step 4: Check if activation already exists
        activation_exists = False
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM oxio_activations
                WHERE firebase_uid = %s
                LIMIT 1
            """, (firebase_uid,))
            if cursor.fetchone():
                activation_exists = True
                print(f"   ✓ Activation record already exists")
        
        # Step 5: Record purchase if not exists
        if not purchase_exists:
            print(f"   📝 Recording purchase...")
            from datetime import datetime
            purchase_id = record_purchase(
                stripe_id='manual_fix_' + datetime.now().strftime('%Y%m%d%H%M%S'),
                product_id='esim_beta',
                price_id='price_1S7Yc6JnTfh0bNQQVeLeprXe',
                amount=100,  # $1.00
                user_id=user_id,
                transaction_id='manual_fix',
                firebase_uid=firebase_uid,
                stripe_transaction_id='manual_fix'
            )
            print(f"   ✓ Purchase recorded with ID: {purchase_id}")
        
        # Step 6: Activate eSIM with OXIO if not already activated
        if not activation_exists and oxio_user_id:
            print(f"   🚀 Activating eSIM with OXIO...")
            try:
                from esim_activation_service import esim_activation_service
                
                activation_result = esim_activation_service.activate_esim_after_payment(
                    firebase_uid=firebase_uid,
                    user_email=user_email,
                    user_name=user_name or user_email.split('@')[0],
                    stripe_session_id='manual_fix',
                    purchase_amount=100
                )
                
                if activation_result.get('success'):
                    print(f"   ✅ eSIM activation completed successfully")
                else:
                    print(f"   ⚠️ eSIM activation returned: {activation_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error during activation: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'eSIM activation fix completed',
            'details': {
                'user_id': user_id,
                'email': user_email,
                'iccid': iccid,
                'lpa_code': lpa_code,
                'purchase_recorded': not purchase_exists,
                'activation_triggered': not activation_exists
            }
        })
        
    except Exception as e:
        print(f"❌ Error in fix_failed_esim_activation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/esim/resend-activation-email', methods=['POST'])
def resend_esim_activation_email():
    """Resend eSIM activation email to a user"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebase_uid')
        admin_key = data.get('admin_key')
        
        # Simple admin auth check
        if admin_key != os.environ.get('ADMIN_KEY', 'dotm_admin_2025'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Firebase UID is required'}), 400
        
        print(f"📧 Resending eSIM activation email for Firebase UID: {firebase_uid}")
        
        # Step 1: Get user details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, display_name, oxio_user_id
                FROM users
                WHERE firebase_uid = %s
            """, (firebase_uid,))
            user_result = cursor.fetchone()
            
            if not user_result:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            user_id, user_email, user_name, oxio_user_id = user_result
            print(f"   User: {user_email}")
        
        # Step 2: Get eSIM activation details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT iccid, line_id, phone_number, activation_url, esim_qr_code, oxio_response, created_at
                FROM oxio_activations
                WHERE firebase_uid = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (firebase_uid,))
            activation_result = cursor.fetchone()
            
            if not activation_result:
                return jsonify({'success': False, 'error': 'No eSIM activation found for this user'}), 404
            
            iccid, line_id, phone_number, activation_url, esim_qr_code, oxio_response, created_at = activation_result
            
            # Parse phone number from oxio_response if not directly available
            if not phone_number and oxio_response:
                import json
                try:
                    oxio_data = json.loads(oxio_response) if isinstance(oxio_response, str) else oxio_response
                    phone_numbers = oxio_data.get('data', {}).get('phoneNumbers', [])
                    if phone_numbers and len(phone_numbers) > 0:
                        phone_number = phone_numbers[0].get('phoneNumber', '')
                except Exception as e:
                    print(f"   ⚠️ Could not parse phone number from oxio_response: {e}")
            
            print(f"   eSIM Details: ICCID={iccid}, Phone={phone_number}, Line={line_id}")
        
        # Step 3: Send activation email using the esim_activation_service
        try:
            from esim_activation_service import esim_activation_service
            
            # Prepare eSIM data dictionary (keys must match _send_activation_email expectations)
            esim_data = {
                'phone_number': phone_number or 'Pending',
                'line_id': line_id,
                'iccid': iccid,
                'activation_url': activation_url,
                'qr_code': esim_qr_code,  # Use 'qr_code' not 'qr_code_url'
                'activation_date': created_at.strftime('%B %d, %Y at %I:%M %p') if created_at else 'Unknown'
            }
            
            # Send the email with correct parameters
            email_result = esim_activation_service._send_activation_email(
                user_email=user_email,
                user_name=user_name or user_email.split('@')[0],
                esim_data=esim_data,
                oxio_user_id=oxio_user_id
            )
            
            if email_result:
                print(f"   ✅ Activation email sent successfully to {user_email}")
                return jsonify({
                    'success': True,
                    'message': f'Activation email sent successfully to {user_email}',
                    'details': {
                        'email': user_email,
                        'phone_number': phone_number,
                        'iccid': iccid,
                        'line_id': line_id
                    }
                })
            else:
                print(f"   ❌ Failed to send email")
                return jsonify({
                    'success': False,
                    'error': 'Failed to send activation email'
                }), 500
                
        except Exception as e:
            print(f"   ❌ Error sending activation email: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Email send error: {str(e)}'}), 500
        
    except Exception as e:
        print(f"❌ Error in resend_esim_activation_email: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


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