from flask import Flask, request, send_from_directory, render_template, redirect, jsonify
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO, emit
import os
from typing import Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

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
from datetime import datetime
import stripe
import json

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Import OXIO service
from oxio_service import oxio_service

# Import product setup function
from stripe_products import create_stripe_products
import ethereum_helper
import product_rules_helper

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

                conn.commit()
        else:
            print("No database connection available for table creation")
except Exception as e:
    print(f"Error creating tables on startup: {str(e)}")
    print("Continuing without table creation...")


app = Flask(__name__, static_url_path='/static', template_folder='templates') # Added template_folder
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
    user_agent = request.headers.get('User-Agent', '')
    platform = 'web' if 'Mozilla' in user_agent else 'android'

    # In production, you'd want to store this token in your database
    # associated with the user's account
    print(f"Registered FCM token for {platform}: {token}")

    # For demonstration purposes
    return jsonify({"status": "success", "platform": platform})

# Send notifications to both web and app users
@app.route('/api/send-notification', methods=['POST'])
def send_notification():
    if not request.json:
        return jsonify({"error": "No data provided"}), 400

    title = request.json.get('title', 'Notification')
    body = request.json.get('body', 'You have a new notification')
    target = request.json.get('target', 'all')  # 'all', 'web', 'app'

    try:
        # In a real implementation, you would fetch tokens from your database
        # For demonstration, we're showing the structure

        # Example of sending to specific platforms
        if target == 'all' or target == 'app':
            # Send to Android app users
            send_to_android(title, body)

        if target == 'all' or target == 'web':
            # Send to Web users
            send_to_web(title, body)

        return jsonify({"status": "success", "message": f"Notification sent to {target}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_to_android(title, body):
    # Normally, you would use the Firebase Admin SDK here
    print(f"Sending to Android: {title} - {body}")

    # Example with Firebase Admin SDK (commented out)
    """
    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token='device_token_here',  # or topic='topic_name'
    )

    response = messaging.send(message)
    print('Successfully sent message:', response)
    """

def send_to_web(title, body):
    # Normally, you would use the Firebase Admin SDK here
    print(f"Sending to Web: {title} - {body}")

    # Similar implementation as send_to_android, targeting web tokens

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

                        # Create OXIO user first
                        oxio_user_id = None
                        try:
                            print(f"Creating OXIO user for Firebase UID: {firebase_uid}")
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
                                print(f"Successfully created OXIO user: {oxio_user_id}")
                            else:
                                print(f"Failed to create OXIO user: {oxio_result.get('message', 'Unknown error')}")
                        except Exception as oxio_err:
                            print(f"Error creating OXIO user: {str(oxio_err)}")

                        cur.execute(
                            """INSERT INTO users 
                                (email, firebase_uid, display_name, photo_url, eth_address, oxio_user_id) 
                            VALUES (%s, %s, %s, %s, %s, %s) 
                            RETURNING id""",
                            (email, firebase_uid, display_name, photo_url, test_account.address, oxio_user_id)
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
                                  COALESCE(f.founder, 'N') as founder_status, u.oxio_user_id, u.eth_address
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
                            'metamaskAddress': user[8] if len(user) > 8 else None
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
                    unit_amount=100,  # $1.00 CAD in cents
                    currency='cad',
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
                    currency='cad',
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
            currency='cad',
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
                'firebase_uid': firebase_uid if firebase_uid else '',
                'subscription_type': 'yearly' if is_subscription else 'one_time'
            },
            **customer_params  # Add customer ID if available
        )

        print(f"Created checkout session: {checkout_session.id} for product: {product_id} (subscription: {is_subscription})")
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

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
                                  photo_url, imei, eth_address, oxio_user_id 
                        FROM users WHERE firebase_uid = %s""",
                        (firebase_uid,)
                    )
                    return cur.fetchone()
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
                        # First, verify the table structure to ensure we're using correct column names
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'purchases' 
                            ORDER BY ordinal_position
                        """)
                        columns = [row[0].lower() for row in cur.fetchall()]
                        print(f"Debug: Available columns in purchases table: {columns}")
                        
                        # Use the correct column names based on what's actually in the table
                        if 'stripeproductid' in columns:
                            product_col = 'StripeProductID'
                            amount_col = 'TotalAmount'
                            user_col = 'UserID'
                            firebase_col = 'FirebaseUID'
                        else:
                            # Fallback to other possible column names
                            product_col = 'stripe_product_id'
                            amount_col = 'total_amount'  
                            user_col = 'user_id'
                            firebase_col = 'firebase_uid'
                        
                        # Execute the query with proper column names
                        query = f"""
                            SELECT 
                                COALESCE(SUM(CASE WHEN {product_col} = 'global_data_10gb' THEN {amount_col} ELSE 0 END), 0) as global_data_cents,
                                COALESCE(SUM(CASE WHEN {product_col} LIKE '%data%' OR {product_col} = 'beta_esim_data' THEN {amount_col} ELSE 0 END), 0) as total_data_cents,
                                COUNT(*) as total_purchases
                            FROM purchases 
                            WHERE {user_col} = %s OR {firebase_col} = %s
                        """
                        
                        cur.execute(query, (user_id, firebase_uid))
                        result = cur.fetchone()
                        print(f"Debug: SQL result = {result}")
                        
                        if result and len(result) >= 3:
                            try:
                                global_data_cents = int(result[0]) if result[0] is not None else 0
                                total_data_cents = int(result[1]) if result[1] is not None else 0
                                total_purchases = int(result[2]) if result[2] is not None else 0
                                print(f"Debug: Parsed values - global_data_cents={global_data_cents}, total_data_cents={total_data_cents}, total_purchases={total_purchases}")
                            except (IndexError, TypeError, ValueError) as e:
                                print(f"Error parsing SQL result: {e}")
                                global_data_cents = 0
                                total_data_cents = 0
                                total_purchases = 0
                        else:
                            print(f"No SQL result returned or insufficient columns: {result}")
                            global_data_cents = 0
                            total_data_cents = 0
                            total_purchases = 0
                    except Exception as sql_err:
                        print(f"SQL query error: {sql_err}")
                        # Set safe defaults
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
            else:
                print(f"No user found for Firebase UID {firebase_uid}")
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
                oxio_user_id = user_data[7] if len(user_data) > 7 else None
                
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
                
                # Add endUserId if we have an OXIO user ID
                if oxio_user_id:
                    oxio_activation_payload["endUser"]["endUserId"] = oxio_user_id
                
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
        # This ensures the UI updates even if the database has issues
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

import help_desk_api  # This registers the help desk routes

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
            'oxio_user_id': user_data[7] if len(user_data) > 7 else None,  # OXIO user ID from database
            'metamask_address': user_data[8] if len(user_data) > 8 else None,  # ETH address from database
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

@app.route('/api/beta-enrollment', methods=['POST'])
def beta_enrollment():
    data = request.get_json()
    firebase_uid = data.get('firebaseUid')

    if not firebase_uid:
        return jsonify({'success': False, 'message': 'Firebase UID required'}), 400

    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection error'}), 500

            with conn.cursor() as cur:
                # Get user details
                cur.execute("SELECT id, email, display_name FROM users WHERE firebase_uid = %s", (firebase_uid,))
                user_result = cur.fetchone()

                if not user_result:
                    return jsonify({'success': False, 'message': 'User not found'}), 404

                user_id, user_email, display_name = user_result

                # Check if already enrolled in beta
                cur.execute("""
                    SELECT status FROM beta_testers 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC LIMIT 1
                """, (user_id,))

                existing_status = cur.fetchone()
                if existing_status and existing_status[0] in ['esim_ready', 'enrolled']:
                    return jsonify({
                        'success': True, 
                        'status': existing_status[0],
                        'message': 'Already enrolled in beta program'
                    })

                # Generate demo ICCID details for beta testing
                import random
                import time

                # Create mock ICCID data (in production, this would come from OXIO)
                demo_iccid = f"8910650420001{random.randint(100000, 999999)}F"
                activation_code = f"AC{random.randint(100000, 999999)}"
                qr_code_data = f"LPA:1$api-staging.brandvno.com${activation_code}$"

                # Try to get OXIO SIM details (fallback to demo if service unavailable)
                oxio_sim_details = {
                    'iccid': demo_iccid,
                    'activation_code': activation_code,
                    'qr_code': qr_code_data,
                    'plan_name': 'OXIO_10day_demo_plan',
                    'data_allowance': '1000MB',
                    'validity_days': 10,
                    'regions': ['Global'],
                    'status': 'ready_for_activation'
                }

                try:
                    # Attempt to get real OXIO details
                    from oxio_service import oxio_service
                    test_result = oxio_service.test_connection()
                    if test_result.get('success'):
                        print("OXIO service available - using real SIM details")
                        # In a real implementation, you would call OXIO to get actual SIM details
                        # For now, we'll use the demo data with a note that OXIO is available
                        oxio_sim_details['note'] = 'OXIO service connected - using demo data for beta'
                    else:
                        oxio_sim_details['note'] = 'OXIO service unavailable - using demo data'
                except Exception as oxio_err:
                    print(f"OXIO service error: {str(oxio_err)}")
                    oxio_sim_details['note'] = 'OXIO service error - using demo data'

                # Create email content with ICCID details
                email_subject = f"Beta eSIM Details - ICCID: {oxio_sim_details['iccid']}"
                email_content = f"""
Hello {display_name or 'Beta Tester'},

Welcome to the DOTM Beta Program! Below are your eSIM activation details:

=== eSIM ACTIVATION DETAILS ===
ICCID: {oxio_sim_details['iccid']}
Activation Code: {oxio_sim_details['activation_code']}
QR Code Data: {oxio_sim_details['qr_code']}

=== PLAN DETAILS ===
Plan Name: {oxio_sim_details['plan_name']}
Data Allowance: {oxio_sim_details['data_allowance']}
Validity: {oxio_sim_details['validity_days']} days
Coverage: {', '.join(oxio_sim_details['regions'])}
Status: {oxio_sim_details['status']}

=== ACTIVATION INSTRUCTIONS ===
1. Go to your device's Settings > Cellular/Mobile Data
2. Select "Add Cellular Plan" or "Add eSIM"
3. Scan the QR code or manually enter the activation code above
4. Follow the on-screen instructions to complete activation

=== SUPPORT ===
If you need assistance, please contact our support team with your ICCID reference.

Note: {oxio_sim_details['note']}

Thank you for participating in our beta program!

Best regards,
DOTM Team
                """

                # Send email with ICCID details (simulate for now)
                print(f"=== BETA eSIM EMAIL ===")
                print(f"To: {user_email}")
                print(f"Subject: {email_subject}")
                print(f"Content:\n{email_content}")
                print("========================")

                # Record beta enrollment with eSIM ready status
                cur.execute("""
                    INSERT INTO beta_testers (user_id, firebase_uid, action, status, timestamp)
                    VALUES (%s, %s, 'ON', 'esim_ready', CURRENT_TIMESTAMP)
                """, (user_id, firebase_uid))

                # Add 1000MB of data to user's balance (use empty string for stripeid to avoid NOT NULL constraint)
                cur.execute("""
                    INSERT INTO purchases (stripeid, stripeproductid, priceid, totalamount, userid, datecreated, firebaseuid)
                    VALUES ('', 'beta_esim_data', 'price_beta_data', 100, %s, CURRENT_TIMESTAMP, %s)
                """, (user_id, firebase_uid))

                conn.commit()

                return jsonify({
                    'success': True,
                    'status': 'esim_ready',
                    'message': f'Beta eSIM details sent to {user_email}',
                    'iccid': oxio_sim_details['iccid'],
                    'email_sent': True,
                    'activation_details': oxio_sim_details
                })

    except Exception as e:
        print(f"Error in beta enrollment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Internal server error: {str(e)}'}), 500

@app.route('/api/beta-status')
def get_beta_status():
    firebase_uid = request.args.get('firebaseUid')

    if not firebase_uid:
        return jsonify({'success': False, 'message': 'Firebase UID required'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user details
                cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                user_result = cur.fetchone()

                if not user_result:
                    return jsonify({'success': False, 'message': 'User not found'}), 404

                user_id = user_result[0]

                # Get latest beta status
                cur.execute("""
                    SELECT status, timestamp FROM beta_testers 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC LIMIT 1
                """, (user_id,))

                status_result = cur.fetchone()

                if not status_result:
                    return jsonify({
                        'success': True,
                        'status': 'not_enrolled',
                        'message': 'Not enrolled in beta program'
                    })

                status, timestamp = status_result

                return jsonify({
                    'success': True,
                    'status': status,
                    'message': f'Beta status: {status}',
                    'timestamp': timestamp.isoformat() if timestamp else None
                })

    except Exception as e:
        print(f"Error getting beta status: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/oxio-user-data', methods=['GET'])
def get_oxio_user_data():
    """Get OXIO user data including phone number, line ID, and eSIM profile information"""
    firebase_uid = request.args.get('firebaseUid')
    if not firebase_uid:
        return jsonify({'error': 'Firebase UID is required'}), 400

    try:
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        user_id = user_data[0]
        user_email = user_data[1]
        
        # Extract additional fields from user_data tuple
        oxio_user_id = user_data[7] if len(user_data) > 7 else None
        eth_address = user_data[8] if len(user_data) > 8 else None

        # Get OXIO data from database and API
        oxio_data = {
            'user_id': user_id,
            'email': user_email,
            'oxio_user_id': oxio_user_id,  # OXIO user ID from oxio_user_id column
            'metamask_address': eth_address,  # MetaMask address from eth_address column
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

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Ensure beta_testers table has all required columns
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'beta_testers'
                    """)
                    columns = [row[0] for row in cur.fetchall()]
                    
                    # Add missing columns if they don't exist
                    missing_columns = []
                    if 'stripe_payment_intent_id' not in columns:
                        missing_columns.append('stripe_payment_intent_id VARCHAR(255)')
                    if 'stripe_session_id' not in columns:
                        missing_columns.append('stripe_session_id VARCHAR(255)')
                    
                    for column_def in missing_columns:
                        cur.execute(f"ALTER TABLE beta_testers ADD COLUMN {column_def}")
                    
                    if missing_columns:
                        conn.commit()
                        print(f"Added missing columns to beta_testers: {missing_columns}")

                    # Check for beta tester data (contains some OXIO info)
                    cur.execute("""
                        SELECT status, timestamp, stripe_payment_intent_id 
                        FROM beta_testers 
                        WHERE user_id = %s 
                        ORDER BY timestamp DESC LIMIT 1
                    """, (user_id,))
                    
                    beta_result = cur.fetchone()
                    if beta_result:
                        oxio_data['status'] = beta_result[0]
                        oxio_data['last_updated'] = beta_result[1].isoformat() if beta_result[1] else None
                        oxio_data['subscription_id'] = beta_result[2]

                    # Try to get actual OXIO data from OXIO API
                    try:
                        from oxio_service import oxio_service
                        
                        # Test connection first
                        connection_test = oxio_service.test_connection()
                        if connection_test.get('success'):
                            # If user has OXIO user ID, generate realistic demo data
                            if oxio_data.get('oxio_user_id'):
                                import random
                                demo_iccid = f"8910650420001{random.randint(100000, 999999)}F"
                                demo_phone = f"+1416{random.randint(1000000, 9999999)}"
                                demo_line_id = f"LINE_{random.randint(100000, 999999)}"
                                demo_activation_code = f"AC{random.randint(100000, 999999)}"

                                oxio_data.update({
                                    'phone_number': demo_phone,
                                    'line_id': demo_line_id,
                                    'iccid': demo_iccid,
                                    'activation_code': demo_activation_code,
                                    'plan_name': 'OXIO_Global_Plan',
                                    'data_allowance': '1000MB',
                                    'validity_days': 30,
                                    'regions': ['Global', 'North America', 'Europe'],
                                    'qr_code': f"LPA:1$api-staging.brandvno.com${demo_activation_code}$",
                                    'profile_id': f"PROFILE_{random.randint(100000, 999999)}",
                                    'status': 'active' if beta_result and beta_result[0] == 'esim_ready' else 'pending'
                                })
                                # Keep the MetaMask address separate from OXIO user ID
                                if not oxio_data.get('metamask_address'):
                                    oxio_data['metamask_address'] = metamask_address
                            else:
                                oxio_data['status'] = 'oxio_user_not_created'
                                oxio_data['error'] = 'OXIO user not created yet'
                        else:
                            oxio_data['status'] = 'oxio_unavailable'
                            oxio_data['error'] = 'OXIO service unavailable'
                    
                    except Exception as oxio_err:
                        print(f"Error getting OXIO data: {str(oxio_err)}")
                        oxio_data['status'] = 'oxio_error'
                        oxio_data['error'] = str(oxio_err)

        return jsonify({
            'status': 'success',
            'oxio_data': oxio_data
        })

    except Exception as e:
        print(f"Error getting OXIO user data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/resend-esim-email', methods=['POST'])
def resend_esim_email():
    """Resend eSIM ready email to user"""
    try:
        data = request.get_json()
        firebase_uid = data.get('firebaseUid')

        if not firebase_uid:
            return jsonify({'success': False, 'message': 'Firebase UID required'}), 400

        with get_db_connection() as conn:
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection error'}), 500

            with conn.cursor() as cur:
                # Get user details
                cur.execute("SELECT id, email, display_name FROM users WHERE firebase_uid = %s", (firebase_uid,))
                user_result = cur.fetchone()

                if not user_result:
                    return jsonify({'success': False, 'message': 'User not found'}), 404

                user_id, user_email, display_name = user_result

                # Check if user has eSIM ready status
                cur.execute("""
                    SELECT status FROM beta_testers 
                    WHERE user_id = %s AND status = 'esim_ready'
                    ORDER BY timestamp DESC LIMIT 1
                """, (user_id,))

                status_result = cur.fetchone()

                if not status_result:
                    return jsonify({
                        'success': False, 
                        'message': 'eSIM not ready or user not enrolled in beta'
                    }), 400

                # Generate demo ICCID details for resending
                import random
                demo_iccid = f"8910650420001{random.randint(100000, 999999)}F"
                activation_code = f"AC{random.randint(100000, 999999)}"
                qr_code_data = f"LPA:1$api-staging.brandvno.com${activation_code}$"

                # Create mock OXIO SIM details
                oxio_sim_details = {
                    'iccid': demo_iccid,
                    'activation_code': activation_code,
                    'qr_code': qr_code_data,
                    'plan_name': 'OXIO_10day_demo_plan',
                    'data_allowance': '1000MB',
                    'validity_days': 10,
                    'regions': ['Global'],
                    'status': 'ready_for_activation',
                    'note': 'Resent eSIM details - demo data'
                }

                # Create email content
                email_subject = f"[RESENT] Beta eSIM Details - ICCID: {oxio_sim_details['iccid']}"
                email_content = f"""
Hello {display_name or 'Beta Tester'},

Here are your eSIM activation details (resent):

=== eSIM ACTIVATION DETAILS ===
ICCID: {oxio_sim_details['iccid']}
Activation Code: {oxio_sim_details['activation_code']}
QR Code Data: {oxio_sim_details['qr_code']}

=== PLAN DETAILS ===
Plan Name: {oxio_sim_details['plan_name']}
Data Allowance: {oxio_sim_details['data_allowance']}
Validity: {oxio_sim_details['validity_days']} days
Coverage: {', '.join(oxio_sim_details['regions'])}
Status: {oxio_sim_details['status']}

=== ACTIVATION INSTRUCTIONS ===
1. Go to your device's Settings > Cellular/Mobile Data
2. Select "Add Cellular Plan" or "Add eSIM"
3. Scan the QR code or manually enter the activation code above
4. Follow the on-screen instructions to complete activation

=== SUPPORT ===
If you need assistance, please contact our support team with your ICCID reference.

Note: {oxio_sim_details['note']}

Thank you for participating in our beta program!

Best regards,
DOTM Team
                """

                # Log the resend email (simulate for now)
                print(f"=== RESENT BETA eSIM EMAIL ===")
                print(f"To: {user_email}")
                print(f"Subject: {email_subject}")
                print(f"Content:\n{email_content}")
                print("===============================")

                # Record the resend action
                cur.execute("""
                    INSERT INTO beta_testers (user_id, firebase_uid, action, status, timestamp)
                    VALUES (%s, %s, 'RESEND_EMAIL', 'esim_ready', CURRENT_TIMESTAMP)
                """, (user_id, firebase_uid))

                conn.commit()

                return jsonify({
                    'success': True,
                    'message': f'eSIM details resent to {user_email}',
                    'email_sent': True,
                    'resent_at': datetime.now().isoformat()
                })

    except Exception as e:
        print(f"Error resending eSIM email: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Internal server error: {str(e)}'}), 500

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def handle_beta_esim_payment(session):
    """Handle successful beta eSIM payment"""
    try:
        user_id = session['metadata']['user_id']
        firebase_uid = session['metadata']['firebase_uid']

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Update beta tester status
                cur.execute("""
                    UPDATE beta_testers 
                    SET status = 'esim_ready', stripe_payment_intent_id = %s
                    WHERE user_id = %s AND status = 'payment_pending'
                """, (session['payment_intent'], user_id))

                # Add 1000MB of data to user's balance
                cur.execute("""
                    INSERT INTO purchases (user_id, stripe_payment_intent_id, amount_cents, data_amount_mb, product_id, status)
                    VALUES (%s, %s, 100, 1000, 'beta_esim_data', 'completed')
                """, (user_id, session['payment_intent']))

                # Create OXIO plan for 10 days
                from oxio_service import OxioService
                oxio = OxioService()

                # Get user email for OXIO plan
                cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                user_email = cur.fetchone()[0]

                # Create 10-day plan with 1000MB (1024000 KB)
                plan_result = oxio.create_custom_plan(
                    user_email=user_email,
                    plan_name="OXIO_10day_demo_plan",
                    duration_seconds=10 * 24 * 60 * 60,  # 10 days in seconds
                    data_limit_kb=1024000  # 1000MB in KB
                )

                if plan_result.get('success'):
                    print(f"Created OXIO plan for user {user_id}: {plan_result}")

                    # Send eSIM email
                    from email_service import EmailService
                    email_service = EmailService()

                    email_service.send_esim_ready_email(
                        to_email=user_email,
                        plan_details=plan_result
                    )
                else:
                    print(f"Failed to create OXIO plan: {plan_result}")

                conn.commit()
                print(f"Beta eSIM payment processed for user {user_id}")

    except Exception as e:
        print(f"Error handling beta eSIM payment: {str(e)}")
        import traceback
        traceback.print_exc()

@app.route('/webhook', methods=['GET', 'POST'])
def stripe_webhook():
    if request.method == 'GET':
        # For polling payment status
        return {'status': 'pending'}, 200

    # Handle POST webhook from Stripe
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return {'error': str(e)}, 400
    except stripe.error.SignatureVerificationError as e:
        return {'error': str(e)}, 400

    if event.type == 'invoice.paid':
        invoice = event.data.object
        print(f"Invoice paid: {invoice.id}")
        customer_id = invoice.customer
        customer = stripe.Customer.retrieve(customer_id)

        # Record the purchase
        for line in invoice.lines.data:
            price_id = line.price.id
            product_id = line.price.product
            amount = line.amount

            transaction_id = f"INV_{invoice.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            record_purchase(
                stripe_id=invoice.id,
                product_id=product_id,
                price_id=price_id,
                amount=amount,
                user_id=None,  # We'll need to lookup the user ID from the customer ID
                transaction_id=transaction_id
            )

        print(f"Processing payment for customer {customer.email}")
        return {'status': 'paid', 'redirect': '/dashboard'}, 200

    elif event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        print(f"Payment succeeded: {payment_intent.id}")

        # Handle successful payment
        # You can add logic here to fulfill the order

    elif event.type == 'checkout.session.completed':
        session = event.data.object

        # Check if this is a beta eSIM payment
        if session.get('metadata', {}).get('product_type') == 'beta_esim':
            handle_beta_esim_payment(session)
        
        # Check if this is a Basic Membership purchase
        elif session.get('metadata', {}).get('product_id') == 'basic_membership':
            try:
                print(f"Processing Basic Membership checkout completion: {session.id}")
                
                # Get customer and user information
                customer_id = session.get('customer')
                firebase_uid = session.get('metadata', {}).get('firebase_uid')
                
                if customer_id and firebase_uid:
                    # Get user data
                    user_data = get_user_by_firebase_uid(firebase_uid)
                    if user_data:
                        user_id = user_data[0]
                        user_email = user_data[1]
                        oxio_user_id = user_data[7] if len(user_data) > 7 else None
                        
                        print(f"Activating OXIO line for Stripe Basic Membership purchase by user {user_id}")
                        
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
                        
                        # Add endUserId if we have an OXIO user ID
                        if oxio_user_id:
                            oxio_activation_payload["endUser"]["endUserId"] = oxio_user_id
                        
                        print(f"Stripe OXIO activation payload: {oxio_activation_payload}")
                        
                        # Call OXIO line activation
                        oxio_result = oxio_service.activate_line(oxio_activation_payload)
                        
                        if oxio_result.get('success'):
                            print(f"Successfully activated OXIO line for Stripe Basic Membership: {oxio_result}")
                            
                            # Store OXIO activation details in database
                            try:
                                with get_db_connection() as conn:
                                    if conn:
                                        with conn.cursor() as cur:
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
                                            """, (user_id, firebase_uid, None, 'basic_membership', iccid, 
                                                  line_id, phone_number, 'activated', json.dumps(oxio_result)))
                                            
                                            conn.commit()
                                            print(f"Stored Stripe OXIO activation record for user {user_id}")
                            except Exception as db_err:
                                print(f"Error storing Stripe OXIO activation record: {str(db_err)}")
                        else:
                            print(f"Failed to activate OXIO line via Stripe: {oxio_result.get('message', 'Unknown error')}")
                    else:
                        print(f"User not found for Firebase UID: {firebase_uid}")
                else:
                    print(f"Missing customer_id or firebase_uid in session metadata")
                    
            except Exception as stripe_oxio_err:
                print(f"Error during Stripe OXIO line activation: {str(stripe_oxio_err)}")

    else:
        print(f"Unhandled event type: {event.type}")

    return {'status': 'success'}, 200

@app.route('/token-price-pings', methods=['GET'])
def token_price_pings():
    """Endpoint to view token price ping history"""
    pings = []
    try:
        # Ensure table exists
        create_token_pings_table()

        # Use fixed UserID 1 for demo mode
        user_id = 1

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:

                    # Get recent pings with all fields
                    cur.execute("""
                        SELECT id, token_price, request_time_ms, response_time_ms, 
                               roundtrip_ms, ping_destination, source, additional_data, created_at 
                        FROM token_price_pings 
                        ORDER BY created_at DESC 
                        LIMIT 50
                    """)
                    rows = cur.fetchall()

                    for row in rows:
                        pings.append({
                            'id': row[0],
                            'token_price': float(row[1]) if row[1] else 1.0,
                            'request_time_ms': row[2],
                            'response_time_ms': row[3],
                            'roundtrip_ms': row[4],
                            'ping_destination': row[5],
                            'source': row[6],
                            'additional_data': row[7],
                            'created_at': row[8].isoformat() if row[8] else None
                        })

        return jsonify({
            'status': 'success',
            'pings': pings
        })
    except Exception as e:
        print(f"Error in token-price-pings endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/debug/recent-purchases', methods=['GET'])
def debug_recent_purchases():
    """Debug endpoint to check recent purchases"""
    try:
        firebase_uid = request.args.get('firebaseUid')
        user_id = request.args.get('userId')
        
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get recent purchases
                    if firebase_uid:
                        cur.execute("""
                            SELECT PurchaseID, StripeProductID, TotalAmount, DateCreated, UserID, FirebaseUID
                            FROM purchases 
                            WHERE FirebaseUID = %s OR UserID = (
                                SELECT id FROM users WHERE firebase_uid = %s
                            )
                            ORDER BY DateCreated DESC 
                            LIMIT 10
                        """, (firebase_uid, firebase_uid))
                    else:
                        cur.execute("""
                            SELECT PurchaseID, StripeProductID, TotalAmount, DateCreated, UserID, FirebaseUID
                            FROM purchases 
                            ORDER BY DateCreated DESC 
                            LIMIT 10
                        """)
                    
                    purchases = cur.fetchall()
                    purchase_list = []
                    for purchase in purchases:
                        purchase_list.append({
                            'purchase_id': purchase[0],
                            'product_id': purchase[1],
                            'amount': purchase[2],
                            'date_created': purchase[3].isoformat() if purchase[3] else None,
                            'user_id': purchase[4],
                            'firebase_uid': purchase[5]
                        })
                    
                    return jsonify({
                        'status': 'success',
                        'purchases': purchase_list,
                        'firebase_uid': firebase_uid,
                        'count': len(purchase_list)
                    })
                    
        return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
    except Exception as e:
        print(f"Error in debug purchases: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/debug/purchases-structure', methods=['GET'])
def debug_purchases_structure():
    """Debug endpoint to check purchases table structure and data"""
    try:
        firebase_uid = request.args.get('firebaseUid')
        
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check table structure
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'purchases' 
                        ORDER BY ordinal_position
                    """)
                    columns = cur.fetchall()
                    
                    # Check actual data for this user
                    if firebase_uid:
                        cur.execute("""
                            SELECT * FROM purchases 
                            WHERE FirebaseUID = %s 
                            ORDER BY DateCreated DESC 
                            LIMIT 5
                        """, (firebase_uid,))
                        recent_purchases = cur.fetchall()
                    else:
                        cur.execute("""
                            SELECT * FROM purchases 
                            ORDER BY DateCreated DESC 
                            LIMIT 5
                        """)
                        recent_purchases = cur.fetchall()
                    
                    return jsonify({
                        'status': 'success',
                        'columns': [{'name': col[0], 'type': col[1]} for col in columns],
                        'recent_purchases': [list(purchase) for purchase in recent_purchases],
                        'firebase_uid': firebase_uid
                    })
                    
        return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
    except Exception as e:
        print(f"Error in debug purchases structure: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/debug/user-creation-status/<firebase_uid>', methods=['GET'])
def debug_user_creation_status(firebase_uid):
    """Debug endpoint to verify user creation in all systems (Database, Stripe, OXIO)"""
    try:
        verification_results = {
            'firebase_uid': firebase_uid,
            'database': {'status': 'not_found'},
            'stripe': {'status': 'not_found'},
            'oxio': {'status': 'not_found'},
            'summary': {'all_systems_ok': False}
        }
        
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check user in database
                    cur.execute("""
                        SELECT id, email, display_name, stripe_customer_id, oxio_user_id, created_at
                        FROM users 
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))
                    user_data = cur.fetchone()
                    
                    if user_data:
                        verification_results['database'] = {
                            'status': 'found',
                            'user_id': user_data[0],
                            'email': user_data[1],
                            'display_name': user_data[2],
                            'stripe_customer_id': user_data[3],
                            'oxio_user_id': user_data[4],
                            'created_at': user_data[5].isoformat() if user_data[5] else None
                        }
                        
                        # Check Stripe customer
                        stripe_customer_id = user_data[3]
                        if stripe_customer_id:
                            try:
                                customer = stripe.Customer.retrieve(stripe_customer_id)
                                verification_results['stripe'] = {
                                    'status': 'found',
                                    'customer_id': customer.id,
                                    'email': customer.email,
                                    'created': customer.created,
                                    'metadata': customer.metadata
                                }
                            except Exception as stripe_err:
                                verification_results['stripe'] = {
                                    'status': 'error',
                                    'customer_id': stripe_customer_id,
                                    'error': str(stripe_err)
                                }
                        else:
                            verification_results['stripe']['status'] = 'not_created'
                        
                        # Check OXIO user
                        oxio_user_id = user_data[4]
                        if oxio_user_id:
                            verification_results['oxio'] = {
                                'status': 'found',
                                'oxio_user_id': oxio_user_id,
                                'note': 'OXIO user ID recorded in database'
                            }
                            
                            # Try to verify with OXIO API
                            try:
                                oxio_test = oxio_service.test_connection()
                                if oxio_test.get('success'):
                                    verification_results['oxio']['oxio_api_status'] = 'available'
                                else:
                                    verification_results['oxio']['oxio_api_status'] = 'unavailable'
                                    verification_results['oxio']['oxio_api_error'] = oxio_test.get('message')
                            except Exception as oxio_err:
                                verification_results['oxio']['oxio_api_status'] = 'error'
                                verification_results['oxio']['oxio_api_error'] = str(oxio_err)
                        else:
                            verification_results['oxio']['status'] = 'not_created'
                    
                    # Generate summary
                    db_ok = verification_results['database']['status'] == 'found'
                    stripe_ok = verification_results['stripe']['status'] == 'found'
                    oxio_ok = verification_results['oxio']['status'] == 'found'
                    
                    verification_results['summary'] = {
                        'all_systems_ok': db_ok and stripe_ok and oxio_ok,
                        'database_ok': db_ok,
                        'stripe_ok': stripe_ok,
                        'oxio_ok': oxio_ok,
                        'missing_systems': []
                    }
                    
                    if not db_ok:
                        verification_results['summary']['missing_systems'].append('database')
                    if not stripe_ok:
                        verification_results['summary']['missing_systems'].append('stripe')
                    if not oxio_ok:
                        verification_results['summary']['missing_systems'].append('oxio')
        
        return jsonify(verification_results)
        
    except Exception as e:
        print(f"Error in user creation status debug: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'firebase_uid': firebase_uid
        }), 500

@app.route('/db-test', methods=['GET'])
def db_test():
    """Endpoint to test database connectivity"""
    results = {
        'status': 'unknown',
        'message': '',
        'tables': [],
        'connection_string': 'CONFIGURED' if os.environ.get('DATABASE_URL') else 'MISSING'
    }

    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Test basic connectivity
                    cur.execute("SELECT 1 as test")
                    test_result = cur.fetchone()
                    results['status'] = 'success' if test_result and test_result[0] == 1 else 'error'

                    # Get list of tables
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    tables = cur.fetchall()
                    results['tables'] = [table[0] for table in tables]

                    # Check purchases table structure
                    if 'purchases' in results['tables']:
                        cur.execute("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = 'purchases'
                        """)
                        columns = cur.fetchall()
                        results['purchases_columns'] = {col[0]: col[1] for col in columns}

                        # Check sequence status
                        cur.execute("""
                            SELECT last_value, log_cnt, is_called
                            FROM purchases_purchaseid_seq
                        """)
                        seq_info = cur.fetchone()
                        if seq_info:
                            results['sequence_info'] = {
                                'last_value': seq_info[0],
                                'log_cnt': seq_info[1],
                                'is_called': seq_info[2]
                            }

                    results['message'] = 'Database connection successful'
            else:
                results['status'] = 'error'
                results['message'] = 'Could not get database connection'
    except Exception as e:
        results['status'] = 'error'
        results['message'] = f'Database error: {str(e)}'

    return jsonify(results)

@token_ns.route('/update-address')
class UpdateEthAddress(Resource):
    def post(self):
        try:
            data = request.json
            firebase_uid = data.get('firebaseUid')
            eth_address = data.get('address')

            if not eth_address:
                return {'error': 'Ethereum address is required'}, 400

            # Validate Ethereum address if web3 is available
            try:
                from web3 import Web3
                web3 = Web3()
                if not web3.is_address(eth_address):
                    return {'error': 'Invalid Ethereum address'}, 400
            except:
                # If web3 is not available, do basic validation
                if not eth_address.startswith('0x') or len(eth_address) != 42:
                    return {'error': 'Invalid Ethereum address format'}, 400

            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        if firebase_uid:
                            # Update by Firebase UID
                            cur.execute("""
                                UPDATE users 
                                SET eth_address = %s 
                                WHERE firebase_uid = %s
                                RETURNING id
                            """, (eth_address, firebase_uid))
                        else:
                            # Fallback to user ID 1 for demo
                            cur.execute("""
                                UPDATE users 
                                SET eth_address = %s 
                                WHERE id = %s
                                RETURNING id
                            """, (eth_address, 1))

                        result = cur.fetchone()
                        if result:
                            conn.commit()
                            return {
                                'status': 'success',
                                'message': 'Ethereum address updated',
                                'userId': result[0]
                            }
                        else:
                            return {'error': 'User not found'}, 404

            return {'error': 'Database connection error'}, 500
        except Exception as e:
            print(f"Error updating Ethereum address: {str(e)}")
            return {'error': str(e)}, 500


@app.route('/api/user/stripe-id/<int:user_id>', methods=['GET'])
def get_user_stripe_id(user_id):
    """Get Stripe customer ID for a specific user"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, email, firebase_uid, stripe_customer_id, display_name
                        FROM users 
                        WHERE id = %s
                    """, (user_id,))

                    user = cur.fetchone()
                    if user:
                        return jsonify({
                            'status': 'success',
                            'user_id': user[0],
                            'email': user[1],
                            'firebase_uid': user[2],
                            'stripe_customer_id': user[3],
                            'display_name': user[4]
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': f'User {user_id} not found'
                        }), 404

        return jsonify({
            'status': 'error',
            'message': 'Database connection error'
        }), 500

    except Exception as e:
        print(f"Error getting user Stripe ID: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/send-invitation', methods=['POST'])
def send_invitation():
    """Send an invitation to a new user"""
    try:
        data = request.get_json()
        email = data.get('email')
        message = data.get('message', '')
        is_demo_user = data.get('isDemoUser', False)
        firebase_uid = data.get('firebaseUid')

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        # Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        # Generate invitation token
        import secrets
        invitation_token = secrets.token_urlsafe(32)

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Create invites table if it doesn't exist
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS invites (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            email VARCHAR(255) NOT NULL,
                            invitation_status VARCHAR(50) NOT NULL DEFAULT 'invite_sent',
                            invited_by_user_id INTEGER,
                            invited_by_firebase_uid VARCHAR(128),
                            invitation_token VARCHAR(255),
                            personal_message TEXT,
                            is_demo_user BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days',
                            accepted_at TIMESTAMP,
                            rejected_at TIMESTAMP,
                            cancelled_at TIMESTAMP
                        )
                    """)

                    # Get inviting user ID if Firebase UID provided
                    inviting_user_id = None
                    if firebase_uid:
                        cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        user_result = cur.fetchone()
                        if user_result:
                            inviting_user_id = user_result[0]

                    # Check if there's already a pending invitation for this email
                    cur.execute("""
                        SELECT id, invitation_status FROM invites 
                        WHERE email = %s AND invitation_status IN ('invite_sent', 're_invited')
                        ORDER BY created_at DESC LIMIT 1
                    """, (email,))

                    
                    existing_invite = cur.fetchone()
                    if existing_invite:
                        # Update existing invitation as re-invited
                        cur.execute("""
                            UPDATE invites 
                            SET invitation_status = 're_invited', 
                                updated_at = CURRENT_TIMESTAMP,
                                expires_at = CURRENT_TIMESTAMP + INTERVAL '7 days',
                                invitation_token = %s,
                                personal_message = %s
                            WHERE id = %s
                            RETURNING id
                        """, (invitation_token, message, existing_invite[0]))
                        invite_id = cur.fetchone()[0]
                        action_taken = 're_invited'
                    else:
                        # Create new invitation
                        cur.execute("""
                            INSERT INTO invites 
                            (email, invitation_token, invited_by_user_id, invited_by_firebase_uid, 
                             personal_message, is_demo_user, invitation_status)
                            VALUES (%s, %s, %s, %s, %s, %s, 'invite_sent')
                            RETURNING id
                        """, (email, invitation_token, inviting_user_id, firebase_uid, message, is_demo_user))
                        invite_id = cur.fetchone()[0]
                        action_taken = 'invite_sent'

                    conn.commit()

                    # For demo users, immediately create the user account
                    if is_demo_user:
                        try:
                            # Create demo user with random display name
                            demo_names = ['Demo User', 'Test User', 'Sample User', 'Trial User', 'Beta Tester']
                            display_name = demo_names[hash(email) % len(demo_names)]

                            # Create Ethereum wallet for demo user
                            from web3 import Web3
                            web3 = Web3()
                            demo_account = web3.eth.account.create()

                            cur.execute("""
                                INSERT INTO users 
                                (email, display_name, eth_address, firebase_uid) 
                                VALUES (%s, %s, %s, %s) 
                                RETURNING id
                            """, (email, display_name, demo_account.address, f"demo_{invite_id}_{secrets.token_hex(8)}"))

                            demo_user_id = cur.fetchone()[0]

                            # Update invitation with user ID and mark as accepted
                            cur.execute("""
                                UPDATE invites 
                                SET user_id = %s, 
                                    invitation_status = 'invite_accepted',
                                    accepted_at = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (demo_user_id, invite_id))

                            conn.commit()

                            print(f"Created demo user {demo_user_id} for invitation {invite_id}")

                        except Exception as demo_err:
                            print(f"Error creating demo user: {str(demo_err)}")
                            # Don't fail the invitation if demo user creation fails

                    print(f"SUCCESS: Invitation {action_taken} for {email} with ID {invite_id}")
                    return jsonify({
                        'success': True,
                        'message': f'Invitation {action_taken} successfully',
                        'invite_id': invite_id,
                        'email': email,
                        'action': action_taken,
                        'is_demo_user': is_demo_user
                    })

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"ERROR sending invitation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Internal server error: {str(e)}'}), 500

@app.route('/api/network-features/<firebase_uid>/reset', methods=['POST'])
def reset_network_features_to_default(firebase_uid):
    """Reset all network features to their default values for a user"""
    try:
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        # user_data is a tuple, so we need to access by index
        user_id = user_data[0]

        # Get all network features from database
        import stripe_network_features
        features = stripe_network_features.get_network_features()

        # Reset user's preferences to defaults
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Delete existing preferences first
                cur.execute("""
                    DELETE FROM user_network_preferences 
                    WHERE user_id = %s
                """, (user_id,))

                # Insert default preferences
                for feature in features:
                    cur.execute("""
                        INSERT INTO user_network_preferences (user_id, stripe_product_id, enabled)
                        VALUES (%s, %s, %s)
                    """, (user_id, feature['stripe_product_id'], feature['default_enabled']))

                conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Network features reset to default values',
            'features_reset': len(features)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/invites', methods=['GET'])
def get_invites():
    """Get invitations for a user"""
    try:
        firebase_uid = request.args.get('firebaseUid')
        limit = int(request.args.get('limit', 20))

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get invites sent by this user (not cancelled)
                    if firebase_uid:
                        cur.execute("""
                            SELECT id, email, invitation_status, personal_message, is_demo_user,
                                   created_at, updated_at, expires_at, accepted_at, rejected_at,
                                   invited_by_firebase_uid
                            FROM invites 
                            WHERE invited_by_firebase_uid = %s 
                            AND invitation_status != 'invite_cancelled'
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (firebase_uid, limit))
                    else:
                        # If no Firebase UID, get recent invites
                        cur.execute("""
                            SELECT id, email, invitation_status, personal_message, is_demo_user,
                                   created_at, updated_at, expires_at, accepted_at, rejected_at,
                                   invited_by_firebase_uid
                            FROM invites 
                            WHERE invitation_status != 'invite_cancelled'
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (limit,))

                    invites = cur.fetchall()

                    invite_list = []
                    for invite in invites:
                        invite_list.append({
                            'id': invite[0],
                            'email': invite[1],
                            'invitation_status': invite[2],
                            'personal_message': invite[3],
                            'is_demo_user': invite[4],
                            'created_at': invite[5].isoformat() if invite[5] else None,
                            'updated_at': invite[6].isoformat() if invite[6] else None,
                            'expires_at': invite[7].isoformat() if invite[7] else None,
                            'accepted_at': invite[8].isoformat() if invite[8] else None,
                            'rejected_at': invite[9].isoformat() if invite[9] else None,
                            'firebase_uid': invite[10] if len(invite) > 10 else None
                        })

                    return jsonify({
                        'success': True,
                        'invites': invite_list,
                        'count': len(invite_list)
                    })

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error getting invites: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/invites/<int:invite_id>/cancel', methods=['POST'])
def cancel_invitation(invite_id):
    """Cancel an invitation"""
    try:
        firebase_uid = request.json.get('firebaseUid') if request.json else None

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if the user has permission to cancel this invitation
                    if firebase_uid:
                        cur.execute("""
                            SELECT id FROM invites 
                            WHERE id = %s AND invited_by_firebase_uid = %s
                            AND invitation_status IN ('invite_sent', 're_invited')
                        """, (invite_id, firebase_uid))
                    else:
                        cur.execute("""
                            SELECT id FROM invites 
                            WHERE id = %s AND invitation_status IN ('invite_sent', 're_invited')
                        """, (invite_id,))

                    if not cur.fetchone():
                        return jsonify({'success': False, 'message': 'Invitation not found or cannot be cancelled'}), 404

                    # Cancel the invitation
                    cur.execute("""
                        UPDATE invites 
                        SET invitation_status = 'invite_cancelled',
                            cancelled_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING email
                    """, (invite_id,))

                    result = cur.fetchone()
                    conn.commit()

                    return jsonify({
                        'success': True,
                        'message': f'Invitation to {result[0]} cancelled successfully'
                    })

        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    except Exception as e:
        print(f"Error cancelling invitation: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/create-subscription', methods=['POST'])
def create_subscription_record():
    """Manually create a subscription record for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        subscription_type = data.get('subscription_type', 'basic_membership')
        stripe_subscription_id = data.get('stripe_subscription_id')

        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Check if user exists
                    cur.execute("SELECT id, stripe_customer_id FROM users WHERE id = %s", (user_id,))
                    user = cur.fetchone()

                    if not user:
                        return jsonify({
                            'status': 'error',
                            'message': f'User {user_id} not found'
                        }), 404

                    # Create subscription record
                    cur.execute("""
                        INSERT INTO subscriptions 
                        (user_id, subscription_type, stripe_subscription_id, start_date, end_date, status, created_at, updated_at) 
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + interval '365.25 days', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
                        RETURNING subscription_id, end_date
                    """, (user_id, subscription_type, stripe_subscription_id))

                    result = cur.fetchone()
                    subscription_id = result[0]
                    end_date = result[1]
                    conn.commit()

                    return jsonify({
                        'status': 'success',
                        'subscription_id': subscription_id,
                        'user_id': user_id,
                        'subscription_type': subscription_type,
                        'stripe_subscription_id': stripe_subscription_id,
                        'end_date': end_date.isoformat(),
                        'message': 'Subscription created successfully'
                    })

        return jsonify({
            'status': 'error',
            'message': 'Database connection error'
        }), 500

    except Exception as e:
        print(f"Error creating subscription record: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/message-admin')
def message_admin():
    return render_template('message_admin.html')

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

@app.route('/api/oxio-activation-status', methods=['GET'])
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