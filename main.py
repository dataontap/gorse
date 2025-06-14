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

                conn.commit()
        else:
            print("No database connection available for table creation")
except Exception as e:
    print(f"Error creating tables on startup: {str(e)}")
    print("Continuing without table creation...")


app = Flask(__name__, static_url_path='/static', template_folder='templates') # Added template_folder
socketio = SocketIO(app, cors_allowed_origins="*")
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
                        # Create users table with correct column names
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
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        conn.commit()
                        print("Users table created with Firebase fields")

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

                        cur.execute(
                            """INSERT INTO users 
                                (email, firebase_uid, display_name, photo_url, eth_address) 
                            VALUES (%s, %s, %s, %s, %s) 
                            RETURNING id""",
                            (email, firebase_uid, display_name, photo_url, test_account.address)
                        )
                        user_id = cur.fetchone()[0]
                        conn.commit()
                        print(f"New Firebase user created: {user_id} with Sepolia wallet: {test_account.address}")

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
                                    metadata={'firebase_uid': firebase_uid, 'user_id': user_id}
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
                    cur.execute(
                        """SELECT id, email, display_name, photo_url, imei, stripe_customer_id 
                        FROM users WHERE firebase_uid = %s""",
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
                            'stripeCustomerId': user[5]
                        })

                    return jsonify({'error': 'User not found'}), 404

        return jsonify({'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error getting current user: {str(e)}")
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

                    # Get subscription validity for the user
                    cur.execute("""
                        SELECT end_date 
                        FROM subscriptions 
                        WHERE user_id = %s 
                        ORDER BY end_date DESC 
                        LIMIT 1
                    """, (1,))  # Assuming user_id = 1 for demo

                    subscription_result = cur.fetchone()
                    subscription_validity = subscription_result[0].isoformat() if subscription_result else None

                    return jsonify({
                        'count': count,
                        'subscription_validity': subscription_validity
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
                                    # Don't fail the purchase, just log it

                            # Use default user_id if still not found
                            if not user_id:
                                user_id = 1
                                print(f"Using default user_id: {user_id}")

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
                    auto_advance=False,  # Don't finalize yet
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

    elif event.type == 'checkout.session.completed':
        session = event.data.object
        print(f"Checkout completed: {session.id}")

        try:
            # For both one-time payments and subscriptions, record the purchase
            line_items = stripe.checkout.Session.list_line_items(session.id)

            print(f"Processing {len(line_items.data)} line items for session {session.id}")

            for item in line_items.data:
                try:
                    # Get the price object to access product details
                    price = stripe.Price.retrieve(item.price.id)
                    price_id = price.id
                    product_id = price.product
                    amount = item.amount_total

                    # Get user ID and Firebase UID from Stripe customer and session metadata
                    customer_id = session.customer
                    user_id = None
                    firebase_uid = None

                    # Extract Firebase UID from session metadata
                    if hasattr(session, 'metadata') and session.metadata:
                        firebase_uid = session.metadata.get('firebase_uid')

                    if customer_id:
                        try:
                            with get_db_connection() as conn:
                                if conn:
                                    with conn.cursor() as cur:
                                        # Try to get both user ID and Firebase UID from customer
                                        cur.execute("SELECT id, firebase_uid FROM users WHERE stripe_customer_id = %s", (customer_id,))
                                        user_result = cur.fetchone()
                                        if user_result:
                                            user_id = user_result[0]
                                            if not firebase_uid and user_result[1]:
                                                firebase_uid = user_result[1]
                                            print(f"Found user {user_id} with Firebase UID {firebase_uid} for Stripe customer {customer_id}")
                        except Exception as e:
                            print(f"Error looking up user by customer ID: {str(e)}")

                    transaction_id = f"SESS_{session.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    stripe_transaction_id = session.id  # Use session ID as Stripe transaction ID

                    purchase_id = record_purchase(
                        stripe_id=session.id,
                        product_id=product_id,
                        price_id=price_id,
                        amount=amount,
                        user_id=user_id,
                        transaction_id=transaction_id,
                        firebase_uid=firebase_uid,
                        stripe_transaction_id=stripe_transaction_id
                    )

                    # Create subscription for membership products
                    if product_id in ['basic_membership', 'full_membership']:
                        subscription_end_date = create_subscription(
                            user_id=user_id,
                            subscription_type=product_id,
                            stripe_subscription_id=session.subscription if hasattr(session, 'subscription') else None,
                            firebase_uid=firebase_uid
                        )
                        print(f"Created subscription for user {user_id} (Firebase UID: {firebase_uid}), product {product_id}, valid until {subscription_end_date}")

                    # Award tokens based on product rules
                    try:
                        product_rules = product_rules_helper.get_product_rules(product_id)
                        if product_rules:
                            reward_percentage = product_rules['token_reward_percentage'] / 100.0  # Convert to decimal
                            token_reward = amount * reward_percentage / 100  # amount is in cents

                            # Get user's wallet address and award tokens
                            # For now, use a default wallet for demo
                            print(f"Would award {token_reward} tokens for product {product_id} based on {product_rules['token_reward_percentage']}% rule")
                        else:
                            print(f"No product rules found for {product_id}")
                    except Exception as token_err:
                        print(f"Error awarding tokens based on product rules: {str(token_err)}")

                    print(f"Recorded purchase {purchase_id} for product {product_id}, price {price_id}, amount {amount} with Stripe transaction {stripe_transaction_id}")
                except Exception as e:
                    print(f"Error processing line item: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error processing checkout session: {str(e)}")

        return {'status': 'paid', 'redirect': '/dashboard'}, 200

    elif event.type == 'invoice.payment_failed':
        invoice = event.data.object
        print(f"Invoice payment failed: {invoice.id}")
        return {'status': 'failed'}, 200

    return {'status': 'pending'}, 200


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

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
                                  photo_url, imei, eth_address 
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

    # Default user_id for fallback
    user_id = 1

    try:
        # If Firebase UID is provided, look up the internal user ID
        if firebase_uid:
            user_data = get_user_by_firebase_uid(firebase_uid)
            if user_data:
                user_id = user_data[0]  # Get the actual internal user ID (integer)
                stripe_customer_id = user_data[3]  # Get Stripe customer ID
                print(f"Found user {user_id} for Firebase UID {firebase_uid} with Stripe customer {stripe_customer_id}")
            else:
                print(f"No user found for Firebase UID {firebase_uid}, using default user_id=1")
        elif user_id_param and user_id_param.isdigit():
            # If a numeric user ID is provided, use it
            user_id = int(user_id_param)
            print(f"Using provided numeric user_id: {user_id}")
        else:
            print(f"Invalid or no user identifier provided, using default user_id=1")

        # Get total global data purchases for this user using internal user ID
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get total global data purchases using internal UserID
                    cur.execute("""
                        SELECT SUM(TotalAmount) 
                        FROM purchases 
                        WHERE StripeProductID = 'global_data_10gb' AND UserID = %s
                    """, (user_id,))

                    result = cur.fetchone()
                    total_amount = result[0] if result and result[0] else 0

                    # Convert cents to dollars and then to data amount (10GB per $10)
                    data_amount = (total_amount / 100) * 1.0  # 1GB per dollar

                    print(f"Data balance lookup: user_id={user_id}, total_amount={total_amount}, data_amount={data_amount}")

                    return jsonify({
                        'userId': user_id,
                        'firebaseUid': firebase_uid,
                        'dataBalance': data_amount,
                        'unit': 'GB',
                        'billing_type': 'purchase_based',
                        'note': 'Future releases will include real-time usage tracking with Stripe metering'
                    })

        return jsonify({
            'userId': user_id,
            'firebaseUid': firebase_uid,
            'dataBalance': 0,
            'unit': 'GB',
            'error': 'No database connection'
        })

    except Exception as e:
        print(f"Error getting user data balance: {str(e)}")
        return jsonify({
            'userId': user_id,
            'firebaseUid': firebase_uid,
            'dataBalance': 0,
            'unit': 'GB',
            'error': str(e)
        })

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

    # Record the purchase with Firebase UID
    purchase_id = record_purchase(
        stripe_id=None,  # No stripe id in this case
        product_id=product_id,
        price_id=price_id,
        amount=amount,
        user_id=None,  # Will be looked up from Firebase UID
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

    if purchase_id:
        print(f"Successfully recorded purchase: {purchase_id} for product: {product_id} with Firebase UID: {firebase_uid}")
        return {'status': 'success', 'purchaseId': purchase_id}
    else:
        print(f"Failed to record purchase for product: {product_id}")
        # For demo purposes, we'll still create a simulated purchase ID
        # This ensures the UI updates even if the database has issues
        simulated_purchase_id = f"SIM_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Created simulated purchase ID: {simulated_purchase_id}")
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

# This duplicate route was removed to fix the conflict
# The route is already defined earlier in the file


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
    """Get the last 10 Ethereum transactions for the current user"""
    try:
        user_id = request.args.get('userId', '1')

        # Get user's Ethereum address from database
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT eth_address FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()

                    if not result or not result[0]:
                        return jsonify({
                            'status': 'error',
                            'message': 'No Ethereum address found for user',
                            'transactions': []
                        })

                    eth_address = result[0]

        # Fetch transactions from Sepolia using Web3
        from ethereum_helper import get_web3_connection
        web3 = get_web3_connection()

        # Get latest block number
        latest_block = web3.eth.get_block('latest')
        latest_block_number = latest_block['number']

        transactions = []
        blocks_to_check = 1000  # Check last 1000 blocks

        # Search through recent blocks for transactions involving this address
        for block_num in range(max(0, latest_block_number - blocks_to_check), latest_block_number + 1):
            try:
                block = web3.eth.get_block(block_num, full_transactions=True)

                for tx in block['transactions']:
                    if (tx['to'] and tx['to'].lower() == eth_address.lower()) or \
                       (tx['from'] and tx['from'].lower() == eth_address.lower()):

                        # Convert values for display
                        value_eth = web3.from_wei(tx['value'], 'ether')
                        gas_price_gwei = web3.from_wei(tx['gasPrice'], 'gwei') if tx['gasPrice'] else 0

                        transactions.append({
                            'hash': tx['hash'].hex(),
                            'block_number': tx['blockNumber'],
                            'from': tx['from'],
                            'to': tx['to'],
                            'value': str(value_eth),
                            'gas': tx['gas'],
                            'gas_price': str(gas_price_gwei),
                            'timestamp': block['timestamp'],
                            'type': 'received' if (tx['to'] and tx['to'].lower() == eth_address.lower()) else 'sent'
                        })

                        if len(transactions) >= 10:
                            break

                if len(transactions) >= 10:
                    break

            except Exception as block_err:
                print(f"Error fetching block {block_num}: {str(block_err)}")
                continue

        # Sort by block number (most recent first)
        transactions.sort(key=lambda x: x['block_number'], reverse=True)

        return jsonify({
            'status': 'success',
            'address': eth_address,
            'network': 'sepolia',
            'transactions': transactions[:10]
        })

    except Exception as e:
        print(f"Error fetching Ethereum transactions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'transactions': []
        })

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on http://0.0.0.0:{port}")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        # Fallback to standard Flask run
        app.run(host='0.0.0.0', port=port, debug=True)
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

# OXIO API Integration Endpoints
oxio_ns = api.namespace('oxio', description='OXIO API operations')

@oxio_ns.route('/test-connection')
class OXIOTestConnection(Resource):
    def get(self):
        """Test OXIO API connection and credentials"""
        try:
            result = oxio_service.test_connection()
            status_code = 200 if result['success'] else 400
            return result, status_code
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test OXIO connection'
            }, 500

@oxio_ns.route('/activate-line')
class OXIOActivateLine(Resource):
    def post(self):
        """Activate a line using OXIO API"""
        try:
            data = request.get_json()
            if not data:
                return {
                    'success': False,
                    'error': 'No payload provided',
                    'message': 'Request body is required'
                }, 400

            # You can add payload validation here if needed
            required_fields = ['lineType', 'sim', 'endUser', 'countryCode']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}',
                        'message': f'Field {field} is required in the payload'
                    }, 400

            result = oxio_service.activate_line(data)
            status_code = 200 if result['success'] else (result.get('status_code', 400))
            
            return result, status_code
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to activate line'
            }, 500

@oxio_ns.route('/test-sample-activation')
class OXIOTestSampleActivation(Resource):
    def post(self):
        """Test line activation with the provided sample payload"""
        try:
            # Use the sample payload you provided
            sample_payload = {
                "lineType": "LINE_TYPE_MOBILITY",
                "sim": {
                    "simType": "EMBEDDED",
                    "iccid": "8910650420001501340F"
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
            
            # Allow override of payload values from request
            data = request.get_json()
            if data:
                # Merge any provided fields with the sample payload
                sample_payload.update(data)
            
            result = oxio_service.activate_line(sample_payload)
            status_code = 200 if result['success'] else (result.get('status_code', 400))
            
            # Add the payload used for reference
            result['payload_used'] = sample_payload
            
            return result, status_code
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test sample activation'
            }, 500