from flask import Flask, request, send_from_directory
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO, emit
import os
from typing import Optional
from replit import db
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
cred = credentials.Certificate('firebase-credentials.json')
firebase_admin.initialize_app(cred)

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
            
            esim_download_link = "https://your-esim-download-link.com"  # Replace with actual link
            
            if data['method'] == 'sms':
                message = messaging.Message(
                    notification=messaging.Notification(
                        title='Your eSIM is ready',
                        body='Here is your link to download the eSIM and connect to dot network'
                    ),
                    data={
                        'esim_link': esim_download_link
                    },
                    token=data['contact']  # This should be a Firebase token for SMS
                )
                response = messaging.send(message)
                
            elif data['method'] == 'email':
                # Use Firebase Dynamic Links or Custom Email Handler
                # Implementation depends on your Firebase configuration
                pass
                
            return {
                'message': f'eSIM sent via {data["method"]} to {data["contact"]}',
                'status': 'success'
            }
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

@app.route('/', endpoint='serve_index')
def serve_index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)