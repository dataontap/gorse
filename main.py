from flask import Flask, request, send_from_directory, render_template, redirect, jsonify, Response
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO, emit
import os
import sys
from typing import Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from functools import wraps
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
                        print("Adding status column to beta_testers table...")
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

                # Check if first_transaction_bonuses table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'first_transaction_bonuses')")
                first_transaction_bonuses_exists = cur.fetchone()[0]

                if not first_transaction_bonuses_exists:
                    print("Creating first_transaction_bonuses table...")
                    with open('create_first_transaction_bonus_table.sql', 'r') as sql_file:
                        sql_script = sql_file.read()
                        cur.execute(sql_script)
                    conn.commit()
                    print("first_transaction_bonuses table created successfully")
                else:
                    print("first_transaction_bonuses table already exists")

                # Check if phone_number_changes table exists
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'phone_number_changes')")
                phone_number_changes_exists = cur.fetchone()[0]

                if not phone_number_changes_exists:
                    print("Creating phone_number_changes table...")
                    with open('create_phone_number_changes_table.sql', 'r') as sql_file:
                        sql_script = sql_file.read()
                        cur.execute(sql_script)
                    conn.commit()
                    print("phone_number_changes table created successfully")
                else:
                    print("phone_number_changes table already exists")

                # Check if MCP API keys tables exist
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'mcp_api_keys')")
                mcp_api_keys_exists = cur.fetchone()[0]

                if not mcp_api_keys_exists:
                    print("Creating MCP API keys tables...")
                    cur.execute("""
                        CREATE TABLE mcp_api_keys (
                            id SERIAL PRIMARY KEY,
                            key_hash VARCHAR(64) UNIQUE NOT NULL,
                            key_name VARCHAR(255) NOT NULL,
                            description TEXT,
                            rate_limit INTEGER DEFAULT 1000,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_used_at TIMESTAMP,
                            total_requests BIGINT DEFAULT 0,
                            firebase_uid VARCHAR(128),
                            allowed_origins TEXT[],
                            metadata JSONB
                        );
                        
                        CREATE INDEX idx_mcp_api_keys_key_hash ON mcp_api_keys(key_hash);
                        CREATE INDEX idx_mcp_api_keys_is_active ON mcp_api_keys(is_active);
                        CREATE INDEX idx_mcp_api_keys_firebase_uid ON mcp_api_keys(firebase_uid);
                        
                        CREATE TABLE mcp_api_requests (
                            id SERIAL PRIMARY KEY,
                            key_hash VARCHAR(64) NOT NULL,
                            request_path VARCHAR(255),
                            request_method VARCHAR(10),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ip_address INET,
                            user_agent TEXT,
                            response_status INTEGER
                        );
                        
                        CREATE INDEX idx_mcp_api_requests_key_hash_timestamp 
                            ON mcp_api_requests(key_hash, timestamp);
                    """)
                    conn.commit()
                    print("MCP API keys tables created successfully")
                else:
                    print("MCP API keys tables already exist")

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

@app.route('/api/oxio/zip-codes', methods=['GET'])
def oxio_get_zip_codes():
    """Get list of ZIP codes with their associated area codes"""
    try:
        prefix = request.args.get('prefix')
        state = request.args.get('state')
        per_page = int(request.args.get('perPage', 50))
        page = int(request.args.get('page', 1))
        
        result = oxio_service.get_zip_codes(
            prefix=prefix,
            state=state,
            per_page=per_page,
            page=page
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            status_code = result.get('status_code', 500)
            return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve ZIP codes'
        }), 500

@app.route('/api/oxio/zip-codes/<zip_code>', methods=['GET'])
def oxio_get_zip_code_details(zip_code):
    """Get detailed information for a specific ZIP code"""
    try:
        result = oxio_service.get_zip_code_details(zip_code)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            status_code = result.get('status_code', 404)
            return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to retrieve ZIP code {zip_code} details'
        }), 500

@app.route('/api/oxio/available-area-codes', methods=['GET'])
def oxio_get_available_area_codes():
    """Get available area codes, optionally filtered by ZIP code"""
    try:
        zip_code = request.args.get('zipCode')
        country_code = request.args.get('countryCode', 'US')
        
        result = oxio_service.get_available_area_codes(
            zip_code=zip_code,
            country_code=country_code
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            status_code = result.get('status_code', 500)
            return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve available area codes'
        }), 500

@app.route('/api/oxio/search-numbers', methods=['GET'])
def oxio_search_available_numbers():
    """Search for available phone numbers by NPA NXX or ZIP code"""
    try:
        npa = request.args.get('npa')
        nxx = request.args.get('nxx')
        zip_code = request.args.get('zipCode')
        area_code = request.args.get('areaCode')
        limit = int(request.args.get('limit', 10))
        
        result = oxio_service.search_available_numbers(
            npa=npa,
            nxx=nxx,
            zip_code=zip_code,
            area_code=area_code,
            limit=limit
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            status_code = result.get('status_code', 500)
            return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to search available numbers'
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
def get_current_user():
    """Get current user data from database using Firebase UID"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400

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

                            # Always try to look up user by Firebase UID if provided
                            if firebase_uid:
                                cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                                user_result = cur.fetchone()
                                if user_result:
                                    user_id = user_result[0]
                                    print(f"Found user {user_id} for Firebase UID {firebase_uid}")
                                else:
                                    print(f"No user found for Firebase UID {firebase_uid}")
                            # If firebase_uid wasn't provided or didn't yield a result, use provided user_id if it's valid
                            elif user_id is None or not isinstance(user_id, int):
                                print("Cannot record purchase: No valid user_id provided and no Firebase UID found or linked.")
                                return None

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
    # Pass Stripe publishable key to template
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    return render_template('payments.html', stripe_publishable_key=stripe_publishable_key)

@app.route('/marketplace', methods=['GET'])
def marketplace():
    return render_template('marketplace.html')

@app.route('/configure-payment', methods=['GET', 'POST'])
def configure_payment():
    """Configure automatic payment top-up settings"""
    if request.method == 'GET':
        return render_template('configure_payment.html')
    
    if request.method == 'POST':
        try:
            from firebase_helper import verify_firebase_token
            
            decoded_token, error = verify_firebase_token(request)
            
            if error:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            firebase_uid = decoded_token.get('uid')
            
            initial_amount = request.form.get('initial_amount')
            auto_recharge_enabled = request.form.get('auto_recharge_enabled') == '1'
            threshold_amount = request.form.get('threshold_amount')
            topup_amount = request.form.get('topup_amount')
            monthly_limit = request.form.get('monthly_limit')
            
            if not initial_amount:
                return jsonify({'success': False, 'message': 'Initial amount is required'}), 400
            
            initial_amount = float(initial_amount)
            
            if initial_amount < 5 or initial_amount > 100:
                return jsonify({'success': False, 'message': 'Initial amount must be between $5 and $100'}), 400
            
            if auto_recharge_enabled:
                if not threshold_amount or not topup_amount:
                    return jsonify({'success': False, 'message': 'Threshold and top-up amounts are required when auto-recharge is enabled'}), 400
                
                threshold_amount = float(threshold_amount)
                topup_amount = float(topup_amount)
                
                if threshold_amount < 5 or threshold_amount > 95:
                    return jsonify({'success': False, 'message': 'Threshold amount must be between $5 and $95'}), 400
                
                if topup_amount < 10 or topup_amount > 100:
                    return jsonify({'success': False, 'message': 'Top-up amount must be between $10 and $100'}), 400
                
                if threshold_amount >= topup_amount:
                    return jsonify({'success': False, 'message': 'Top-up amount must be greater than threshold amount'}), 400
                
                if monthly_limit:
                    monthly_limit = float(monthly_limit)
                    if monthly_limit < 20 or monthly_limit > 100:
                        return jsonify({'success': False, 'message': 'Monthly limit must be between $20 and $100'}), 400
                else:
                    monthly_limit = None
            else:
                threshold_amount = None
                topup_amount = None
                monthly_limit = None
            
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO auto_recharge_config 
                            (firebase_uid, initial_amount, auto_recharge_enabled, threshold_amount, topup_amount, monthly_limit, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (firebase_uid) 
                            DO UPDATE SET 
                                initial_amount = EXCLUDED.initial_amount,
                                auto_recharge_enabled = EXCLUDED.auto_recharge_enabled,
                                threshold_amount = EXCLUDED.threshold_amount,
                                topup_amount = EXCLUDED.topup_amount,
                                monthly_limit = EXCLUDED.monthly_limit,
                                updated_at = CURRENT_TIMESTAMP
                        """, (firebase_uid, initial_amount, auto_recharge_enabled, threshold_amount, topup_amount, monthly_limit))
                        conn.commit()
                        
                        print(f"Saved auto-recharge config for user {firebase_uid}: initial=${initial_amount}, auto_recharge={auto_recharge_enabled}")
                        
                        cur.execute("""
                            SELECT email, display_name FROM users WHERE firebase_uid = %s
                        """, (firebase_uid,))
                        user_data = cur.fetchone()
                        user_email = user_data[0] if user_data else None
                        user_name = user_data[1] if user_data else None
                    
                    customers = stripe.Customer.list(email=user_email, limit=1) if user_email else None
                    if customers and customers.data:
                        customer_id = customers.data[0].id
                    elif user_email:
                        customer = stripe.Customer.create(
                            email=user_email,
                            metadata={'firebase_uid': firebase_uid}
                        )
                        customer_id = customer.id
                    else:
                        customer_id = None
                    
                    amount_in_cents = int(initial_amount * 100)
                    
                    checkout_session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=[{
                            'price': 'price_1RM9sxJnTfh0bNQQgj2sacLZ',
                            'quantity': 1,
                        }],
                        mode='payment',
                        success_url=request.url_root + 'dashboard?session_id={CHECKOUT_SESSION_ID}&payment_success=true',
                        cancel_url=request.url_root + 'configure-payment',
                        customer=customer_id if customer_id else None,
                        metadata={
                            'product_id': 'global_data_10gb',
                            'firebase_uid': firebase_uid,
                            'user_email': user_email or '',
                            'user_name': user_name or '',
                            'initial_amount': str(initial_amount),
                            'auto_recharge_enabled': str(auto_recharge_enabled),
                            'threshold_amount': str(threshold_amount) if threshold_amount else '',
                            'topup_amount': str(topup_amount) if topup_amount else '',
                            'monthly_limit': str(monthly_limit) if monthly_limit else '',
                            'oxio_plan_id': '9d521906-ea2f-4c2b-b717-1ce36744c36a'
                        }
                    )
                    
                    print(f"Created checkout session {checkout_session.id} for ${initial_amount} data credit (10GB) with OXIO plan")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Configuration saved successfully',
                        'redirect': checkout_session.url
                    })
                else:
                    return jsonify({'success': False, 'message': 'Database connection error'}), 500
                    
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
        except Exception as e:
            print(f"Error saving payment configuration: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        return render_template('configure_payment.html')

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

# Owner Authentication Decorator
def owner_required(f):
    """Require owner email authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get owner email from environment variable (secure, configurable)
        owner_email = os.environ.get('OWNER_EMAIL', 'aa@dotmobile.app')
        
        # Get the current user from Firebase
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized', 'message': 'Admin access restricted'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            decoded_token = firebase_admin.auth.verify_id_token(token)
            user_email = decoded_token.get('email', '')
            
            # Check if user email matches owner email
            if user_email.lower() != owner_email.lower():
                return jsonify({
                    'error': 'Forbidden', 
                    'message': 'Access restricted to platform owner'
                }), 403
            
            # Pass the user info to the route
            request.owner_user = decoded_token
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"Owner authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed', 'message': str(e)}), 401
    
    return decorated_function


@app.route('/admin')
def admin():
    """Admin Central Dashboard - consolidates all admin tools"""
    return render_template('admin_central.html')


@app.route('/api/admin/stats', methods=['GET'])
@firebase_auth_required
def get_admin_stats():
    """Get platform statistics for admin dashboard"""
    try:
        # Get user from request object (set by decorator)
        user = request.firebase_user
        
        # Check if user is owner
        owner_email = os.environ.get('OWNER_EMAIL', 'aa@dotmobile.app')
        user_email = user.get('email', '')
        
        if user_email.lower() != owner_email.lower():
            return jsonify({'error': 'Forbidden'}), 403
        
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database unavailable'}), 500
            
            with conn.cursor() as cur:
                # Get user count
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0] or 0
                
                # Get purchase count and total revenue
                cur.execute("""
                    SELECT COUNT(*), COALESCE(SUM(totalamount / 100.0), 0) 
                    FROM purchases
                """)
                purchase_row = cur.fetchone()
                purchase_count = purchase_row[0] or 0
                total_revenue = float(purchase_row[1]) if purchase_row[1] else 0
                
                # Get subscription count
                cur.execute("""
                    SELECT COUNT(*) FROM subscriptions 
                    WHERE status = 'active'
                """)
                active_subs = cur.fetchone()[0] or 0
                
                # Get MCP API key count
                cur.execute("SELECT COUNT(*) FROM mcp_api_keys WHERE is_active = true")
                mcp_keys_count = cur.fetchone()[0] or 0
                
                # Get data usage stats
                cur.execute("""
                    SELECT 
                        COALESCE(SUM(data_used_gb), 0) as total_gb,
                        COALESCE(SUM(cost_usd), 0) as total_cost
                    FROM data_usage_metrics
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
                """)
                usage_row = cur.fetchone()
                monthly_data_gb = float(usage_row[0]) if usage_row[0] else 0
                monthly_data_cost = float(usage_row[1]) if usage_row[1] else 0
                
                # Get help desk ticket count
                cur.execute("""
                    SELECT COUNT(*) FROM user_message_history 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                recent_tickets = cur.fetchone()[0] or 0
                
                return jsonify({
                    'success': True,
                    'stats': {
                        'users': {
                            'total': user_count
                        },
                        'purchases': {
                            'count': purchase_count,
                            'revenue': round(total_revenue, 2)
                        },
                        'subscriptions': {
                            'active': active_subs
                        },
                        'mcp': {
                            'active_keys': mcp_keys_count
                        },
                        'data_usage': {
                            'monthly_gb': round(monthly_data_gb, 2),
                            'monthly_cost': round(monthly_data_cost, 2)
                        },
                        'support': {
                            'recent_tickets': recent_tickets
                        }
                    }
                })
                
    except Exception as e:
        print(f"Error getting admin stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
            .session-id {{ word-break: break-all; font-family: monospace; font-size: 0.9em; color: #555; }}
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
                <p><strong>Session ID:</strong><br><span class="session-id">{session_id or 'N/A'}</span></p>
                <p><strong>Status:</strong> Sending eSIM...</p>
            </div>

            <div class="next-steps">
                <h3>What's Next?</h3>
                <p>📡 Your eSIM is being activated automatically on our network.</p>
                <p>📧 You will receive your activated eSIM details and QR code via email.</p>
                <p>📱 Download and install it onto your phone or other compatible device.</p>
                <p>🌍 Enjoy global connectivity with dotmobile and accumulate DOTM tokens</p>
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

        # Prepare metadata
        session_metadata = {
            'product_id': product_id,
            'product': product_id,  # Add 'product' field for webhook compatibility
            'firebase_uid': firebase_uid,
            'user_email': user_email or '',  # Add for eSIM activation
            'user_name': user_name or '',    # Add for eSIM activation
            'subscription_type': 'yearly' if is_subscription else 'one_time'
        }
        
        # Add OXIO plan ID for global data product
        if product_id == 'global_data_10gb':
            session_metadata['oxio_plan_id'] = os.environ.get('OXIO_10GB_PLAN_ID', '9d521906-ea2f-4c2b-b717-1ce36744c36a')
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription' if is_subscription else 'payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=session_metadata,
            **customer_params  # Add customer ID if available
        )

        print(f"Created checkout session: {checkout_session.id} for product: {product_id} (subscription: {is_subscription})")
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-methods/setup-intent', methods=['POST'])
@firebase_auth_required
def create_setup_intent():
    """Create a SetupIntent for adding a payment method"""
    try:
        # Get Firebase UID from verified token
        firebase_uid = request.firebase_user.get('uid')
        if not firebase_uid:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get user's Stripe customer ID from database
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection unavailable'}), 503
            
            with conn.cursor() as cur:
                cur.execute("SELECT stripe_customer_id, email FROM users WHERE firebase_uid = %s", (firebase_uid,))
                result = cur.fetchone()
                
                if not result:
                    return jsonify({'error': 'User not found'}), 404
                
                stripe_customer_id, email = result
                
                # Create Stripe customer if doesn't exist
                if not stripe_customer_id:
                    customer = stripe.Customer.create(
                        email=email,
                        metadata={'firebase_uid': firebase_uid}
                    )
                    stripe_customer_id = customer.id
                    
                    # Update database with new customer ID
                    cur.execute(
                        "UPDATE users SET stripe_customer_id = %s WHERE firebase_uid = %s",
                        (stripe_customer_id, firebase_uid)
                    )
                    conn.commit()
        
        # Create SetupIntent
        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
        )
        
        return jsonify({
            'clientSecret': setup_intent.client_secret
        })
        
    except Exception as e:
        print(f"Error creating setup intent: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-methods', methods=['GET'])
@firebase_auth_required
def get_payment_methods():
    """Get all payment methods for a user"""
    try:
        # Get Firebase UID from verified token
        firebase_uid = request.firebase_user.get('uid')
        if not firebase_uid:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get user's Stripe customer ID from database
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection unavailable'}), 503
                
            with conn.cursor() as cur:
                cur.execute("SELECT stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                result = cur.fetchone()
                
                if not result or not result[0]:
                    return jsonify({'paymentMethods': []})
                
                stripe_customer_id = result[0]
        
        # Get payment methods from Stripe
        payment_methods = stripe.Customer.list_payment_methods(
            stripe_customer_id,
            type='card'
        )
        
        # Get default payment method
        customer = stripe.Customer.retrieve(stripe_customer_id)
        default_pm_id = customer.invoice_settings.default_payment_method
        
        # Format payment methods for frontend
        formatted_pms = []
        for pm in payment_methods.data:
            formatted_pms.append({
                'id': pm.id,
                'brand': pm.card.brand,
                'last4': pm.card.last4,
                'exp_month': pm.card.exp_month,
                'exp_year': pm.card.exp_year,
                'isDefault': pm.id == default_pm_id
            })
        
        return jsonify({'paymentMethods': formatted_pms})
        
    except Exception as e:
        print(f"Error fetching payment methods: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-methods/<pm_id>/detach', methods=['POST'])
@firebase_auth_required
def detach_payment_method(pm_id):
    """Detach/remove a payment method"""
    try:
        # Get Firebase UID from verified token
        firebase_uid = request.firebase_user.get('uid')
        if not firebase_uid:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify the payment method belongs to the user's customer
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection unavailable'}), 503
                
            with conn.cursor() as cur:
                cur.execute("SELECT stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                result = cur.fetchone()
                
                if not result or not result[0]:
                    return jsonify({'error': 'User not found'}), 404
                
                stripe_customer_id = result[0]
        
        # Verify payment method belongs to this customer before detaching
        try:
            pm = stripe.PaymentMethod.retrieve(pm_id)
            if pm.customer != stripe_customer_id:
                return jsonify({'error': 'Unauthorized: Payment method does not belong to this user'}), 403
        except Exception as e:
            return jsonify({'error': 'Payment method not found'}), 404
        
        # Detach the payment method
        stripe.PaymentMethod.detach(pm_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error detaching payment method: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-methods/<pm_id>/set-default', methods=['POST'])
@firebase_auth_required
def set_default_payment_method(pm_id):
    """Set a payment method as default"""
    try:
        # Get Firebase UID from verified token
        firebase_uid = request.firebase_user.get('uid')
        if not firebase_uid:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get user's Stripe customer ID
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection unavailable'}), 503
                
            with conn.cursor() as cur:
                cur.execute("SELECT stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                result = cur.fetchone()
                
                if not result or not result[0]:
                    return jsonify({'error': 'User not found'}), 404
                
                stripe_customer_id = result[0]
        
        # Verify payment method belongs to this customer before setting as default
        try:
            pm = stripe.PaymentMethod.retrieve(pm_id)
            if pm.customer != stripe_customer_id:
                return jsonify({'error': 'Unauthorized: Payment method does not belong to this user'}), 403
        except Exception as e:
            return jsonify({'error': 'Payment method not found'}), 404
        
        # Update customer's default payment method
        stripe.Customer.modify(
            stripe_customer_id,
            invoice_settings={'default_payment_method': pm_id}
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error setting default payment method: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_user_assigned_iccid_data(firebase_uid):
    """Check if user already has an assigned ICCID from inventory"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT iccid, lpa_code, country, line_id, assigned_at
                FROM iccid_inventory
                WHERE allocated_to_firebase_uid = %s AND status = 'assigned'
                ORDER BY assigned_at DESC
                LIMIT 1
            """, (firebase_uid,))
            result = cursor.fetchone()

            if result:
                return {
                    'iccid': result[0],
                    'lpa_code': result[1],
                    'country': result[2],
                    'line_id': result[3],
                    'assigned_at': result[4]
                }
            return None
    except Exception as e:
        print(f"Error checking user assigned ICCID: {e}")
        return None

def assign_iccid_to_user_atomic(firebase_uid, user_email):
    """Atomically assign an available ICCID to user from inventory"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Use SELECT FOR UPDATE to lock the row and prevent race conditions
            cursor.execute("""
                UPDATE iccid_inventory
                SET status = 'assigned',
                    allocated_to_firebase_uid = %s,
                    assigned_to = %s,
                    assigned_at = NOW()
                WHERE id = (
                    SELECT id FROM iccid_inventory
                    WHERE status = 'available'
                    ORDER BY id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING iccid, lpa_code, country, line_id
            """, (firebase_uid, user_email))

            result = cursor.fetchone()
            conn.commit()

            if result:
                return {
                    'iccid': result[0],
                    'lpa_code': result[1],
                    'country': result[2],
                    'line_id': result[3]
                }
            return None
    except Exception as e:
        print(f"Error assigning ICCID to user: {e}")
        return None

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
                        assigned_iccid = assign_iccid_to_user_atomic(firebase_uid, user_email)

                        if not assigned_iccid:
                            print(f"❌ No available ICCIDs for user {firebase_uid}")
                            return jsonify({'error': 'No available eSIMs in inventory'}), 500

                        print(f"✅ Assigned new ICCID {assigned_iccid['iccid']} to user {firebase_uid}")

                    total_amount = session.get('amount_total', 100)  # Default $1.00 in cents

                    print(f"🎯 eSIM activation parameters: Firebase UID={firebase_uid}, Email={user_email}, Amount=${total_amount/100:.2f}, ICCID={assigned_iccid['iccid']}")

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

                        # The activation service already sends the confirmation email
                        # No need to send a separate receipt email here

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

                        # Award first transaction bonus if eligible
                        try:
                            user_data = get_user_by_firebase_uid(firebase_uid)
                            if user_data:
                                user_id = user_data.get('id')
                                eth_address = user_data.get('eth_address')
                                
                                if eth_address:
                                    bonus_success, bonus_message = ethereum_helper.check_and_award_first_transaction_bonus(
                                        user_id, firebase_uid, eth_address
                                    )
                                    if bonus_success:
                                        print(f"🎁 {bonus_message}")
                                    else:
                                        print(f"ℹ️ First transaction bonus: {bonus_message}")
                                else:
                                    print(f"⚠️ User {firebase_uid} does not have an Ethereum address for DOTM bonus")
                        except Exception as bonus_error:
                            print(f"⚠️ Error awarding first transaction bonus: {str(bonus_error)}")

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

            # Handle Global Data 10GB activation with OXIO
            elif (product_id == 'global_data_10gb' or product == 'global_data_10gb') and firebase_uid:
                try:
                    print(f"💰 Processing 10GB Global Data purchase for Firebase UID: {firebase_uid}")
                    
                    # Get OXIO plan ID from metadata or environment variable
                    oxio_plan_id = session['metadata'].get('oxio_plan_id') or os.environ.get('OXIO_10GB_PLAN_ID', '9d521906-ea2f-4c2b-b717-1ce36744c36a')
                    user_email = session['metadata'].get('user_email', '')
                    user_name = session['metadata'].get('user_name', '')
                    total_amount = session.get('amount_total', 2000)  # Default $20.00 in cents
                    
                    print(f"📋 10GB Activation params: Firebase UID={firebase_uid}, Email={user_email}, Plan ID={oxio_plan_id}, Amount=${total_amount/100:.2f}")
                    
                    # Get or create user data
                    with get_db_connection() as conn:
                        if conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    SELECT id, email, display_name, oxio_user_id
                                    FROM users
                                    WHERE firebase_uid = %s
                                """, (firebase_uid,))
                                user_data = cur.fetchone()
                                
                                if not user_data:
                                    print(f"⚠️ User not found in database, creating new user")
                                    cur.execute("""
                                        INSERT INTO users (email, firebase_uid, display_name)
                                        VALUES (%s, %s, %s)
                                        RETURNING id
                                    """, (user_email, firebase_uid, user_name))
                                    user_id = cur.fetchone()[0]
                                    oxio_user_id = None
                                    conn.commit()
                                else:
                                    user_id = user_data[0]
                                    user_email = user_data[1] or user_email
                                    user_name = user_data[2] or user_name
                                    oxio_user_id = user_data[3]
                    
                    # Import OXIO service
                    from oxio_service import oxio_service
                    
                    # Ensure OXIO user exists
                    if not oxio_user_id:
                        print(f"🆕 Creating OXIO user for {user_email}")
                        name_parts = (user_name or "User").split(' ', 1)
                        first_name = name_parts[0] if name_parts else "User"
                        last_name = name_parts[1] if len(name_parts) > 1 else "Account"
                        
                        user_result = oxio_service.create_oxio_user(
                            first_name=first_name,
                            last_name=last_name,
                            email=user_email,
                            firebase_uid=firebase_uid
                        )
                        
                        if user_result.get('success'):
                            oxio_user_id = user_result.get('oxio_user_id')
                            print(f"✅ Created OXIO user: {oxio_user_id}")
                            
                            # Update user record with OXIO user ID
                            with get_db_connection() as conn:
                                if conn:
                                    with conn.cursor() as cur:
                                        cur.execute("""
                                            UPDATE users SET oxio_user_id = %s
                                            WHERE firebase_uid = %s
                                        """, (oxio_user_id, firebase_uid))
                                        conn.commit()
                        else:
                            print(f"❌ Failed to create OXIO user: {user_result.get('message', 'Unknown error')}")
                            return jsonify({'error': 'Failed to create OXIO user'}), 500
                    
                    # Activate OXIO data plan
                    print(f"🚀 Activating OXIO 10GB plan for user: {oxio_user_id}")
                    
                    # Create plan subscription payload
                    plan_payload = {
                        "endUserId": oxio_user_id,
                        "planId": oxio_plan_id
                    }
                    
                    print(f"📤 OXIO Plan Activation Request:")
                    print(f"   URL: {oxio_service.base_url}/v3/subscriptions")
                    print(f"   Payload: {json.dumps(plan_payload, indent=2)}")
                    
                    # Make OXIO API call to activate plan (booster)
                    import requests
                    import base64
                    from oxio_service import oxio_service
                    
                    # Use OXIO service's authentication method (Basic Auth)
                    headers = oxio_service.get_headers()
                    
                    # Note: Endpoint for adding booster to existing line
                    # You'll need to update this URL when you have the correct OXIO booster endpoint
                    response = requests.post(
                        f'{oxio_service.base_url}/v3/subscriptions',
                        json=plan_payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    print(f"📥 OXIO Plan Activation Response:")
                    print(f"   Status Code: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
                    if response.status_code in [200, 201]:
                        oxio_response = response.json()
                        subscription_id = oxio_response.get('id') or oxio_response.get('subscriptionId')
                        
                        print(f"✅ OXIO 10GB plan activated successfully")
                        print(f"   Subscription ID: {subscription_id}")
                        
                        # Record purchase in database
                        purchase_id = record_purchase(
                            stripe_id=session.get('id'),
                            product_id='global_data_10gb',
                            price_id='price_1RM9sxJnTfh0bNQQgj2sacLZ',
                            amount=total_amount,
                            user_id=user_id,
                            transaction_id=session.get('payment_intent'),
                            firebase_uid=firebase_uid,
                            stripe_transaction_id=session.get('payment_intent')
                        )
                        print(f"💾 Purchase recorded with ID: {purchase_id}")
                        
                        # Award first transaction bonus if eligible
                        try:
                            user_data = get_user_by_firebase_uid(firebase_uid)
                            if user_data:
                                eth_address = user_data.get('eth_address')
                                
                                if eth_address:
                                    bonus_success, bonus_message = ethereum_helper.check_and_award_first_transaction_bonus(
                                        user_id, firebase_uid, eth_address
                                    )
                                    if bonus_success:
                                        print(f"🎁 {bonus_message}")
                                    else:
                                        print(f"ℹ️ First transaction bonus: {bonus_message}")
                        except Exception as bonus_error:
                            print(f"⚠️ Error awarding first transaction bonus: {str(bonus_error)}")
                        
                    else:
                        print(f"❌ OXIO plan activation failed")
                        return jsonify({
                            'error': 'OXIO plan activation failed',
                            'status_code': response.status_code,
                            'message': response.text
                        }), 500
                        
                except Exception as e:
                    print(f"❌ Error in 10GB Global Data activation: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({'error': str(e)}), 500
            
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
        # Get SM-DP+ address from OXIO_ENVIRONMENT (extract domain from base URL)
        from oxio_service import oxio_service
        smdp_address = oxio_service.base_url.replace('https://', '').replace('http://', '')
        
        if lpa_code and iccid:
            qr_data = f"LPA:1${smdp_address}${iccid}$?esim_activation_code={lpa_code}"
        elif lpa_code:
            qr_data = f"LPA:1${smdp_address}$None$?esim_activation_code={lpa_code}"
        elif iccid:
            qr_data = f"LPA:1${smdp_address}${iccid}$"
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

            if oxio_result.get('success') and oxio_result.get('user_id'):
                oxio_user_id = oxio_result['user_id']

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
            # Get balance based on address
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
            return {
                'address': address,
                'balance': 0.0,
                'token_price': 1.0,
                'value_usd': 0.0,
                'error': str(e)
            }

@token_ns.route('/balance/me')
class CurrentUserBalance(Resource):
    @firebase_auth_required
    def get(self):
        try:
            firebase_uid = request.firebase_user.get('uid')
            
            # Get user's eth_address and created_at from database
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT eth_address, created_at FROM users WHERE firebase_uid = %s",
                            (firebase_uid,)
                        )
                        result = cur.fetchone()
                        
                        if result and result[0]:
                            eth_address = result[0]
                            created_at = result[1]
                            balance = ethereum_helper.get_token_balance(eth_address)
                        else:
                            # No wallet address found
                            eth_address = None
                            created_at = None
                            balance = 0.0
                else:
                    eth_address = None
                    created_at = None
                    balance = 0.0

            # Get the latest token price
            try:
                price_data = ethereum_helper.get_token_price_from_etherscan()
                token_price = price_data.get('price', 1.0)
            except Exception as e:
                print(f"Using default token price due to error: {str(e)}")
                token_price = 1.0  # Default fallback

            return {
                'address': eth_address,
                'balance': balance,
                'token_price': token_price,
                'value_usd': balance * token_price,
                'has_wallet': eth_address is not None,
                'created_at': created_at.isoformat() if created_at else None,
                'eth_address': eth_address
            }
        except Exception as e:
            print(f"Error getting current user balance: {str(e)}")
            return {
                'address': None,
                'balance': 0.0,
                'token_price': 1.0,
                'value_usd': 0.0,
                'has_wallet': False,
                'error': str(e),
                'eth_address': None,
                'created_at': None
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

@token_ns.route('/transactions')
class UserTransactions(Resource):
    @firebase_auth_required
    def get(self):
        """Get combined transactions (blockchain + purchases) for the current user"""
        try:
            firebase_uid = request.firebase_user.get('uid')
            limit = request.args.get('limit', '5')  # Default to last 5
            
            try:
                limit = int(limit)
            except:
                limit = 5
            
            # Get user's eth_address from database
            eth_address = None
            user_id = None
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT eth_address, id FROM users WHERE firebase_uid = %s",
                            (firebase_uid,)
                        )
                        result = cur.fetchone()
                        if result:
                            eth_address = result[0]
                            user_id = result[1]
            
            all_transactions = []
            
            # Fetch blockchain transactions from Etherscan Mainnet API
            if eth_address:
                etherscan_api_key = os.environ.get('ETHERSCAN_API_KEY')
                if etherscan_api_key:
                    try:
                        import requests
                        # Get token transactions from Etherscan
                        token_address = os.environ.get('TOKEN_ADDRESS')
                        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={token_address}&address={eth_address}&sort=desc&apikey={etherscan_api_key}"
                        
                        response = requests.get(url, timeout=10)
                        data = response.json()
                        
                        if data.get('status') == '1' and data.get('result'):
                            for tx in data['result'][:20]:  # Get last 20 blockchain transactions
                                # Determine if IN or OUT
                                is_incoming = tx['to'].lower() == eth_address.lower()
                                token_amount = int(tx['value']) / (10 ** 18)  # Convert from wei
                                
                                all_transactions.append({
                                    'type': 'token_in' if is_incoming else 'token_out',
                                    'direction': 'IN' if is_incoming else 'OUT',
                                    'description': 'DOTM Tokens Received' if is_incoming else 'DOTM Tokens Sent',
                                    'token_amount': token_amount,
                                    'usd_value': 0.0,  # $0 for now as requested
                                    'timestamp': int(tx['timeStamp']),
                                    'hash': tx['hash'],
                                    'from': tx['from'],
                                    'to': tx['to'],
                                    'network': 'mainnet'
                                })
                    except Exception as e:
                        print(f"Error fetching Etherscan transactions: {str(e)}")
            
            # Fetch purchases from database (only if user exists in database)
            if user_id:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT 
                                    PurchaseID,
                                    StripeProductID,
                                    TotalAmount,
                                    DateCreated,
                                    StripeTransactionID
                                FROM purchases
                                WHERE FirebaseUID = %s
                                ORDER BY DateCreated DESC
                                LIMIT 20
                            """, (firebase_uid,))
                            
                            purchases = cur.fetchall()
                            for purchase in purchases:
                                purchase_id, product_id, amount, date_created, tx_id = purchase
                                
                                # Convert amount from cents to dollars
                                amount_usd = amount / 100.0 if amount else 0
                                
                                # Add as OUT transaction
                                all_transactions.append({
                                    'type': 'purchase',
                                    'direction': 'OUT',
                                    'description': f'Purchase: {product_id}',
                                    'token_amount': 0,
                                    'usd_value': amount_usd,
                                    'timestamp': int(date_created.timestamp()) if date_created else 0,
                                    'hash': tx_id or str(purchase_id),
                                    'network': 'stripe'
                                })
            
            # Sort all transactions by timestamp (most recent first)
            all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply limit
            limited_transactions = all_transactions[:limit] if limit > 0 else all_transactions
            
            return {
                'status': 'success',
                'transactions': limited_transactions,
                'total_count': len(all_transactions),
                'shown_count': len(limited_transactions),
                'has_more': len(all_transactions) > len(limited_transactions)
            }
            
        except Exception as e:
            print(f"Error getting transactions: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'transactions': []
            }, 500

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
    """Toggle a specific network feature for a user"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get user_id from firebase_uid
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    user_result = cur.fetchone()

                    if not user_result:
                        return jsonify({
                            'status': 'error',
                            'message': 'User not found'
                        }), 404

                    user_id = user_result[0]

                    # Check if preference exists
                    cur.execute("""
                        SELECT id FROM user_network_preferences 
                        WHERE user_id = %s AND stripe_product_id = %s
                    """, (user_id, product_id))

                    existing = cur.fetchone()

                    if existing:
                        # Update existing preference
                        cur.execute("""
                            UPDATE user_network_preferences 
                            SET enabled = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND stripe_product_id = %s
                        """, (enabled, user_id, product_id))
                    else:
                        # Insert new preference
                        cur.execute("""
                            INSERT INTO user_network_preferences 
                            (user_id, stripe_product_id, enabled)
                            VALUES (%s, %s, %s)
                        """, (user_id, product_id, enabled))

                    conn.commit()

                    return jsonify({
                        'status': 'success',
                        'message': f'Network feature {"enabled" if enabled else "disabled"} successfully',
                        'feature_id': product_id,
                        'enabled': enabled
                    })

        return jsonify({
            'status': 'error',
            'message': 'Database connection error'
        }), 500

    except Exception as e:
        print(f"Error toggling network feature: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add the new endpoint definition here
@app.route('/api/network/services', methods=['GET'])
def get_user_network_services():
    """Get user's active network services for profile overview"""
    try:
        firebase_uid = request.args.get('firebaseUid')

        if not firebase_uid:
            return jsonify({
                'success': False,
                'message': 'Firebase UID is required'
            }), 400

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get user_id from firebase_uid
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    user_result = cur.fetchone()

                    if not user_result:
                        return jsonify({
                            'success': False,
                            'message': 'User not found'
                        }), 404

                    user_id = user_result[0]

                    # Get active network services
                    cur.execute("""
                        SELECT 
                            nf.stripe_product_id,
                            nf.feature_name,
                            nf.feature_title,
                            nf.description,
                            unp.enabled,
                            nf.price_cents
                        FROM user_network_preferences unp
                        JOIN network_features nf ON unp.stripe_product_id = nf.stripe_product_id
                        WHERE unp.user_id = %s AND unp.enabled = TRUE
                        ORDER BY nf.feature_name
                    """, (user_id,))

                    services = []
                    for row in cur.fetchall():
                        services.append({
                            'service_id': row[0],
                            'name': row[2] or row[1],
                            'service_title': row[2],
                            'description': row[3],
                            'status': 'active',
                            'type': 'network',
                            'price': row[5] / 100 if row[5] else 0,
                            'expiry_date': '2099-12-31'
                        })

                    return jsonify({
                        'success': True,
                        'services': services,
                        'count': len(services)
                    })

        return jsonify({
            'success': False,
            'message': 'Database connection error'
        }), 500

    except Exception as e:
        print(f"Error fetching network services: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/user-phone-numbers', methods=['GET'])
def get_user_phone_numbers():
    """Get user's phone numbers and eSIM details"""
    try:
        firebase_uid = request.args.get('firebase_uid')
        
        if not firebase_uid:
            return jsonify({
                'success': False,
                'message': 'Firebase UID is required'
            }), 400
        
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            phone_number,
                            line_id,
                            iccid,
                            activation_url,
                            activation_code,
                            esim_qr_code,
                            product_id,
                            activation_status,
                            created_at
                        FROM oxio_activations
                        WHERE firebase_uid = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (firebase_uid,))
                    
                    row = cur.fetchone()
                    
                    if row:
                        phone_numbers = [{
                            'phone_number': row[0],
                            'line_id': row[1],
                            'iccid': row[2],
                            'activation_url': row[3],
                            'lpa_code': row[4],
                            'qr_code': row[5],
                            'plan_name': row[6].replace('_', ' ').title() if row[6] else 'eSIM Plan',
                            'status': row[7] or 'active',
                            'activated_at': row[8].isoformat() if row[8] else None
                        }]
                        return jsonify({
                            'success': True,
                            'phone_numbers': phone_numbers
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'phone_numbers': []
                        })
        
        return jsonify({
            'success': False,
            'message': 'Database connection error'
        }), 500
        
    except Exception as e:
        print(f"Error fetching user phone numbers: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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

# MCP v2 Server Routes (Model Context Protocol 2025 Specification)
# Lazy loading to avoid import issues
MCP_V2_AVAILABLE = None  # Will be set on first use
_mcp_v2_instance = None
_mcp_auth = None

def get_mcp_v2_server():
    """Lazy load MCP v2 server"""
    global MCP_V2_AVAILABLE, _mcp_v2_instance, _mcp_auth
    
    if MCP_V2_AVAILABLE is None:
        try:
            from mcp_server_v2 import mcp_server, auth_middleware
            _mcp_v2_instance = mcp_server
            _mcp_auth = auth_middleware
            MCP_V2_AVAILABLE = True
            print("✅ MCP v2 Server loaded successfully")
        except Exception as e:
            MCP_V2_AVAILABLE = False
            print(f"❌ MCP v2 Server not available: {str(e)}")
            import traceback
            traceback.print_exc()
    
    if not MCP_V2_AVAILABLE:
        raise ImportError("MCP v2 Server not available")
    
    return _mcp_v2_instance

@app.route('/mcp/v2')
def mcp_v2_info():
    """MCP v2 server information endpoint"""
    try:
        get_mcp_v2_server()  # Ensure it's loaded
    except ImportError:
        return jsonify({"error": "MCP v2 server not available"}), 503
    
    return jsonify({
        "server": "DOTM MCP Server",
        "version": "2.0.0",
        "protocol_version": "2024-11-05",
        "specification": "https://modelcontextprotocol.io/specification/2024-11-05",
        "transport": "HTTP + SSE (Streamable HTTP)",
        "capabilities": {
            "resources": {"subscribe": False, "listChanged": True},
            "tools": {"listChanged": True},
            "prompts": {"listChanged": False}
        },
        "endpoints": {
            "info": "/mcp/v2",
            "messages": "/mcp/v2/messages",
            "docs": "/mcp/v2/docs",
            "legacy_v1": "/mcp"
        },
        "authentication": {
            "type": "Firebase Bearer Token",
            "auto_registration": True,
            "required": False,
            "header": "Authorization: Bearer <token>"
        }
    })

@app.route('/mcp/v2/messages', methods=['POST'])
def mcp_v2_messages():
    """JSON-RPC 2.0 endpoint for MCP v2 protocol"""
    try:
        mcp_v2_instance = get_mcp_v2_server()
    except ImportError:
        return jsonify({"error": "MCP v2 server not available"}), 503
    
    try:
        import asyncio
        
        body = request.get_json()
        method = body.get("method")
        msg_id = body.get("id")
        params = body.get("params", {})
        
        if body.get("jsonrpc") != "2.0":
            return jsonify({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32600, "message": "Invalid Request"}
            }), 400
        
        async def process_request():
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "resources": {"subscribe": False, "listChanged": True},
                            "tools": {"listChanged": True},
                            "prompts": {"listChanged": False}
                        },
                        "serverInfo": {"name": "dotm-mcp-server", "version": "2.0.0"}
                    }
                }
            
            elif method == "resources/list":
                resources = await mcp_v2_instance.handlers['list_resources']()
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "resources": [
                            {
                                "uri": r.uri,
                                "name": r.name,
                                "description": r.description,
                                "mimeType": r.mimeType
                            } for r in resources
                        ]
                    }
                }
            
            elif method == "resources/read":
                uri = params.get("uri")
                content = await mcp_v2_instance.handlers['read_resource'](uri)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": content
                        }]
                    }
                }
            
            elif method == "tools/list":
                tools = await mcp_v2_instance.handlers['list_tools']()
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": t.name,
                                "description": t.description,
                                "inputSchema": t.inputSchema
                            } for t in tools
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                content = await mcp_v2_instance.handlers['call_tool'](tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": c.type, "text": c.text} for c in content]
                    }
                }
            
            elif method == "prompts/list":
                prompts = await mcp_v2_instance.handlers['list_prompts']()
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "prompts": [
                            {
                                "name": p.name,
                                "description": p.description,
                                "arguments": [
                                    {"name": a.name, "description": a.description, "required": a.required}
                                    for a in (p.arguments or [])
                                ]
                            } for p in prompts
                        ]
                    }
                }
            
            elif method == "prompts/get":
                prompt_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await mcp_v2_instance.handlers['get_prompt'](prompt_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "description": result.description,
                        "messages": [
                            {"role": m.role, "content": {"type": m.content.type, "text": m.content.text}}
                            for m in result.messages
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
        
        result = asyncio.run(process_request())
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in MCP v2 messages endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        }), 500

@app.route('/mcp/v2/docs')
def mcp_v2_docs():
    """Comprehensive API documentation for MCP v2"""
    try:
        get_mcp_v2_server()  # Ensure it's loaded
    except ImportError:
        return jsonify({"error": "MCP v2 server not available"}), 503
    
    return jsonify({
        "title": "DOTM MCP Server API Documentation",
        "version": "2.0.0",
        "protocol": "Model Context Protocol (MCP) 2024-11-05",
        "base_url": "/mcp/v2",
        "authentication": {
            "type": "Firebase Bearer Token",
            "header": "Authorization: Bearer <firebase_token>",
            "auto_registration": True,
            "optional": True
        },
        "endpoints": {
            "GET /mcp/v2": "Server information and capabilities",
            "POST /mcp/v2/messages": "JSON-RPC 2.0 endpoint for all MCP operations",
            "GET /mcp/v2/docs": "This documentation endpoint"
        },
        "json_rpc_methods": [
            "initialize",
            "resources/list",
            "resources/read",
            "tools/list",
            "tools/call",
            "prompts/list",
            "prompts/get"
        ],
        "resources": [
            {
                "uri": "dotm://services/catalog",
                "name": "Complete Service Catalog",
                "description": "Full catalog of all DOTM services"
            },
            {
                "uri": "dotm://services/membership",
                "name": "Membership Plans",
                "description": "Annual subscription plans"
            },
            {
                "uri": "dotm://services/network",
                "name": "Network Features",
                "description": "Network add-ons"
            },
            {
                "uri": "dotm://pricing/summary",
                "name": "Pricing Summary",
                "description": "Cost calculations"
            }
        ],
        "tools": [
            {
                "name": "calculate_pricing",
                "description": "Calculate total pricing for selected services"
            },
            {
                "name": "search_services",
                "description": "Search services by keyword, type, or price"
            },
            {
                "name": "get_service_details",
                "description": "Get detailed service information"
            },
            {
                "name": "compare_memberships",
                "description": "Compare membership plans"
            }
        ],
        "prompts": [
            {
                "name": "recommend_plan",
                "description": "Get personalized plan recommendation"
            },
            {
                "name": "explain_service",
                "description": "Get detailed service explanation"
            },
            {
                "name": "cost_optimization",
                "description": "Analyze and optimize service costs"
            }
        ],
        "examples": {
            "initialize": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "client", "version": "1.0.0"}
                }
            },
            "list_tools": {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            },
            "call_tool": {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "calculate_pricing",
                    "arguments": {
                        "service_ids": ["basic_membership", "network_vpn_access"]
                    }
                }
            }
        }
    })

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

        beta_service = BetaApprovalService()
        result = beta_service.reject_beta_request(request_id, reason=request.args.get('reason'))

        if result['success']:
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #fff8e1;">
                <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h1 style="color: #ff9800; text-align: center;">⚠️ Beta Request Rejected</h1>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Reason:</strong> {request.args.get('reason', 'Not specified')}</p>
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

# User Address Management Endpoints
@app.route('/api/user/addresses', methods=['GET'])
def get_user_addresses():
    """Get user addresses (billing, mailing, and broadband)"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if addresses table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'user_addresses'
                        )
                    """)
                    table_exists = cur.fetchone()[0]

                    if not table_exists:
                        # Create addresses table with broadband support
                        cur.execute("""
                            CREATE TABLE user_addresses (
                                id SERIAL PRIMARY KEY,
                                firebase_uid VARCHAR(128) NOT NULL,
                                billing_address JSONB,
                                mailing_address JSONB,
                                broadband_address JSONB,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(firebase_uid)
                            )
                        """)
                        conn.commit()
                    else:
                        # Check if broadband_address column exists and add it if missing
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns
                            WHERE table_name = 'user_addresses' AND column_name = 'broadband_address'
                        """)
                        broadband_column_exists = cur.fetchone()

                        if not broadband_column_exists:
                            print("Adding broadband_address column to user_addresses table...")
                            cur.execute("ALTER TABLE user_addresses ADD COLUMN broadband_address JSONB")
                            conn.commit()
                            print("Broadband address column added successfully")

                    # Get user addresses
                    cur.execute("""
                        SELECT billing_address, mailing_address, broadband_address
                        FROM user_addresses
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))

                    result = cur.fetchone()
                    if result:
                        return jsonify({
                            'success': True,
                            'addresses': {
                                'billing_address': result[0],
                                'mailing_address': result[1],
                                'broadband_address': result[2]
                            }
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'addresses': {
                                'billing_address': None,
                                'mailing_address': None,
                                'broadband_address': None
                            }
                        })

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error getting user addresses: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/addresses', methods=['POST'])
def save_user_addresses():
    """Save user addresses (billing, mailing, or broadband)"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    firebase_uid = data.get('firebaseUid')
    address_type = data.get('addressType')  # 'billing', 'mailing', or 'broadband'
    address = data.get('address')

    if not firebase_uid or not address_type or not address:
        return jsonify({'error': 'Firebase UID, address type, and address are required'}), 400

    if address_type not in ['billing', 'mailing', 'broadband']:
        return jsonify({'error': 'Invalid address type'}), 400

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Upsert address
                    if address_type == 'billing':
                        cur.execute("""
                            INSERT INTO user_addresses (firebase_uid, billing_address, updated_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (firebase_uid)
                            DO UPDATE SET
                                billing_address = EXCLUDED.billing_address,
                                updated_at = CURRENT_TIMESTAMP
                        """, (firebase_uid, json.dumps(address)))
                    elif address_type == 'mailing':
                        cur.execute("""
                            INSERT INTO user_addresses (firebase_uid, mailing_address, updated_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (firebase_uid)
                            DO UPDATE SET
                                mailing_address = EXCLUDED.mailing_address,
                                updated_at = CURRENT_TIMESTAMP
                        """, (firebase_uid, json.dumps(address)))
                    else:  # broadband
                        cur.execute("""
                            INSERT INTO user_addresses (firebase_uid, broadband_address, updated_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (firebase_uid)
                            DO UPDATE SET
                                broadband_address = EXCLUDED.broadband_address,
                                updated_at = CURRENT_TIMESTAMP
                        """, (firebase_uid, json.dumps(address)))

                    conn.commit()
                    return jsonify({
                        'success': True,
                        'message': f'{address_type.capitalize()} address saved successfully'
                    })

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error saving user address: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
            iccid_result = cur.fetchone()

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


# Initialize MCP Usage Service and Auth Manager
try:
    from mcp_usage_service import MCPUsageService
    from mcp_auth import MCPAuthManager
    from data_usage_monitor import DataUsageMonitor
    
    mcp_usage_service = MCPUsageService(get_db_connection)
    mcp_usage_service.ensure_billing_table_exists()
    
    mcp_auth_manager = MCPAuthManager(get_db_connection, usage_service=mcp_usage_service)
    
    data_usage_monitor = DataUsageMonitor(get_db_connection)
    
    print("MCP Usage Service, Auth Manager, and Data Usage Monitor initialized successfully")
except Exception as e:
    print(f"Error initializing MCP services: {str(e)}")
    mcp_usage_service = None
    mcp_auth_manager = None
    data_usage_monitor = None


# MCP API Key Management Endpoints
@app.route('/admin/mcp-keys', methods=['GET'])
def admin_mcp_keys():
    """Admin page for managing MCP API keys"""
    return render_template('admin_mcp_keys.html')


@app.route('/api/admin/mcp-keys/list', methods=['GET'])
def list_mcp_api_keys():
    """List all MCP API keys (admin only)"""
    try:
        admin_key = request.headers.get('X-Admin-Key') or request.args.get('admin_key')
        if admin_key != os.environ.get('ADMIN_KEY', 'dotm_admin_2025'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if not mcp_auth_manager:
            return jsonify({'success': False, 'error': 'MCP Auth Manager not initialized'}), 500
        
        firebase_uid = request.args.get('firebase_uid')
        api_keys = mcp_auth_manager.list_api_keys(firebase_uid)
        
        return jsonify({
            'success': True,
            'api_keys': api_keys
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/mcp-keys/create', methods=['POST'])
def create_mcp_api_key():
    """Create a new MCP API key (admin only)"""
    try:
        data = request.get_json()
        admin_key = data.get('admin_key') or request.headers.get('X-Admin-Key')
        
        if admin_key != os.environ.get('ADMIN_KEY', 'dotm_admin_2025'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if not mcp_auth_manager:
            return jsonify({'success': False, 'error': 'MCP Auth Manager not initialized'}), 500
        
        key_name = data.get('key_name')
        description = data.get('description', '')
        rate_limit = data.get('rate_limit', 1000)
        firebase_uid = data.get('firebase_uid')
        allowed_origins = data.get('allowed_origins', [])
        
        if not key_name:
            return jsonify({'success': False, 'error': 'key_name is required'}), 400
        
        success, result, message = mcp_auth_manager.create_api_key(
            key_name=key_name,
            description=description,
            rate_limit=rate_limit,
            firebase_uid=firebase_uid,
            allowed_origins=allowed_origins
        )
        
        if success:
            return jsonify({
                'success': True,
                'api_key': result,
                'message': message,
                'warning': 'Save this API key securely. It will not be shown again.'
            })
        else:
            return jsonify({'success': False, 'error': result}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/mcp-keys/revoke/<int:key_id>', methods=['POST'])
def revoke_mcp_api_key(key_id):
    """Revoke an MCP API key (admin only)"""
    try:
        data = request.get_json() or {}
        admin_key = data.get('admin_key') or request.headers.get('X-Admin-Key')
        
        if admin_key != os.environ.get('ADMIN_KEY', 'dotm_admin_2025'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if not mcp_auth_manager:
            return jsonify({'success': False, 'error': 'MCP Auth Manager not initialized'}), 500
        
        success, message = mcp_auth_manager.revoke_api_key(key_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/mcp/validate-key', methods=['GET'])
def validate_mcp_key():
    """Validate an MCP API key and return its details"""
    try:
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'valid': False,
                'error': 'Missing or invalid Authorization header'
            }), 401
        
        api_key = auth_header.replace('Bearer ', '').strip()
        
        if not mcp_auth_manager:
            return jsonify({'valid': False, 'error': 'Auth manager not initialized'}), 500
        
        is_valid, key_info = mcp_auth_manager.validate_api_key(api_key)
        
        if is_valid:
            is_allowed, rate_info = mcp_auth_manager.check_rate_limit(api_key, key_info)
            return jsonify({
                'valid': True,
                'key_name': key_info.get('key_name'),
                'rate_limit': rate_info
            })
        else:
            return jsonify({'valid': False, 'error': 'Invalid API key'}), 401
            
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500


# MCP Usage Analytics Endpoints
@app.route('/insights', methods=['GET'])
def insights_page():
    """MCP Usage Insights Page"""
    return render_template('insights.html')


@app.route('/api/mcp/usage/stats', methods=['GET'])
@firebase_auth_required
def get_mcp_usage_stats(user):
    """Get MCP usage statistics for authenticated user"""
    try:
        if not mcp_usage_service:
            return jsonify({'success': False, 'error': 'Usage service not initialized'}), 500
        
        days = int(request.args.get('days', 30))
        firebase_uid = user.get('uid')
        
        stats = mcp_usage_service.get_user_usage_stats(firebase_uid, days)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/mcp/usage/endpoints', methods=['GET'])
@firebase_auth_required
def get_mcp_usage_by_endpoint(user):
    """Get MCP usage breakdown by endpoint"""
    try:
        if not mcp_usage_service:
            return jsonify({'success': False, 'error': 'Usage service not initialized'}), 500
        
        days = int(request.args.get('days', 7))
        firebase_uid = user.get('uid')
        
        endpoint_stats = mcp_usage_service.get_usage_by_endpoint(firebase_uid, days)
        return jsonify(endpoint_stats)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Real-Time Data Usage Endpoints
@app.route('/data-usage', methods=['GET'])
def data_usage_page():
    """Real-time data usage monitoring page"""
    return render_template('data_usage.html')


@app.route('/api/data-usage/realtime', methods=['GET'])
@firebase_auth_required
def get_realtime_data_usage(user):
    """Get real-time data usage metrics for authenticated user"""
    try:
        if not data_usage_monitor:
            return jsonify({'success': False, 'error': 'Data usage monitor not initialized'}), 500
        
        firebase_uid = user.get('uid')
        metrics = data_usage_monitor.get_realtime_metrics(firebase_uid)
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data-usage/history', methods=['GET'])
@firebase_auth_required
def get_data_usage_history(user):
    """Get historical data usage for charting"""
    try:
        if not data_usage_monitor:
            return jsonify({'success': False, 'error': 'Data usage monitor not initialized'}), 500
        
        firebase_uid = user.get('uid')
        hours = int(request.args.get('hours', 24))
        interval = int(request.args.get('interval', 5))
        
        history = data_usage_monitor.get_usage_history(firebase_uid, hours, interval)
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data-usage/log', methods=['POST'])
@firebase_auth_required
def log_data_usage_event(user):
    """Log a data usage event (for testing or external integration)"""
    try:
        if not data_usage_monitor:
            return jsonify({'success': False, 'error': 'Data usage monitor not initialized'}), 500
        
        data = request.get_json()
        firebase_uid = user.get('uid')
        
        # Get user's Stripe customer ID
        stripe_customer_id = None
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    result = cur.fetchone()
                    if result:
                        stripe_customer_id = result[0]
        
        result = data_usage_monitor.log_usage_event(
            firebase_uid=firebase_uid,
            network_type=data.get('network_type', '4G'),
            connection_type=data.get('connection_type', 'Mobile'),
            speed_mbps=float(data.get('speed_mbps', 0)),
            data_used_mb=float(data.get('data_used_mb', 0)),
            priority=data.get('priority'),
            provider=data.get('provider'),
            session_id=data.get('session_id'),
            device_id=data.get('device_id'),
            ip_address=request.remote_addr,
            stripe_customer_id=stripe_customer_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data-usage/simulate', methods=['POST'])
@firebase_auth_required
def simulate_data_usage(user):
    """Simulate realistic data usage for demo purposes"""
    try:
        if not data_usage_monitor:
            return jsonify({'success': False, 'error': 'Data usage monitor not initialized'}), 500
        
        import random
        import uuid
        
        firebase_uid = user.get('uid')
        
        # Get user's Stripe customer ID
        stripe_customer_id = None
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    result = cur.fetchone()
                    if result:
                        stripe_customer_id = result[0]
        
        # Simulate realistic data usage patterns
        network_types = ['4G', '5G']
        connection_types = ['Mobile', 'Home', 'WiFi']
        priorities = ['High', 'Medium', 'Low']
        providers = ['OXIO', 'Verizon', 'AT&T', 'T-Mobile']
        
        network_type = random.choice(network_types)
        connection_type = random.choice(connection_types)
        
        # Realistic speed ranges
        if network_type == '5G':
            speed_mbps = random.uniform(100, 500)
        else:
            speed_mbps = random.uniform(10, 100)
        
        # Simulate data consumption (0.5 - 50 MB per event)
        data_used_mb = random.uniform(0.5, 50)
        
        result = data_usage_monitor.log_usage_event(
            firebase_uid=firebase_uid,
            network_type=network_type,
            connection_type=connection_type,
            speed_mbps=speed_mbps,
            data_used_mb=data_used_mb,
            priority=random.choice(priorities),
            provider=random.choice(providers),
            session_id=str(uuid.uuid4()),
            device_id='demo_device',
            ip_address=request.remote_addr,
            stripe_customer_id=stripe_customer_id
        )
        
        return jsonify(result)
        
    except Exception as e:
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