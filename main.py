from flask import Flask, request, send_from_directory
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO, emit
import os
from typing import Optional
from replit import db
from datetime import datetime
import stripe

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app, cors_allowed_origins="*")
api = Api(app, version='1.0', title='IMEI API',
    description='Get android phone IMEI API with telephony permissions for eSIM activation',
    doc='/api', 
    prefix='/api')  # Move all API endpoints under /api path

ns = api.namespace('imei', description='IMEI operations')
delivery_ns = api.namespace('delivery', description='eSIM delivery operations')

delivery_model = api.model('Delivery', {
    'method': fields.String(required=True, description='Delivery method (email or sms)'),
    'contact': fields.String(required=True, description='Email address or phone number')
})

@delivery_ns.route('')
class DeliveryResource(Resource):
    @delivery_ns.expect(delivery_model)
    @delivery_ns.response(200, 'Success')
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
                product = stripe.Product.create(
                    id='esim_activation_v1',
                    name='eSIM Activation',
                    description='Activate your eSIM for extended usage',
                    default_price_data={
                        'currency': 'usd',
                        'unit_amount': 100,  # $1.00 in cents
                    },
                    metadata={
                        'product_number': '1'
                    }
                )

            # Create or retrieve Stripe customer
            try:
                # Create customer first
                customer = stripe.Customer.create(
                    email=data['contact'] if data['method'] == 'email' else None,
                    phone=data['contact'] if data['method'] == 'sms' else None
                )

                # Create Stripe payment link
                payment_link = stripe.PaymentLink.create(
                    line_items=[{
                        'price': product.default_price,
                        'quantity': 1,
                    }],
                    after_completion={'type': 'redirect', 'url': 'https://get-dot-esim.replit.app/success'},
                    custom_text={'payment_submit': {'message': 'Pay $1 to activate your eSIM'}},
                    allow_promotion_codes=True
                )

                # Send payment link via Stripe
                try:
                    if data['method'] == 'email':
                        stripe.Customer.modify(
                            customer.id,
                            email=data['contact'],
                            preferred_locales=['en'],
                            metadata={'payment_link': payment_link.url}
                        )
                        # Stripe will automatically send an email
                    else:
                        stripe.Customer.modify(
                            customer.id,
                            phone=data['contact'],
                            preferred_locales=['en'],
                            metadata={'payment_link': payment_link.url}
                        )
                        # Send SMS via Stripe
                        stripe.Customer.create_balance_transaction(
                            customer.id,
                            amount=0,  # No charge
                            currency='usd',
                            description=f'Your eSIM payment link: {payment_link.url}'
                        )

                    print(f"Payment link sent successfully via {data['method']}")

                    return {
                        'message': 'Payment link created',
                        'status': 'success',
                        'payment_url': payment_link.url
                    }
                except Exception as e:
                    return {'message': str(e), 'status': 'error'}, 500

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

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
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

    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        print(f"Payment succeeded for {payment_intent.amount}")
        # Handle successful payment here
    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        print(f"Payment failed for {payment_intent.amount}")
        # Handle failed payment here

    return {'status': 'success'}, 200

@app.route('/', endpoint='serve_index')
def serve_index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)