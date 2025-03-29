
from flask import Flask, request
from flask_restx import Api, Resource, fields
from typing import Optional
from replit import db
from datetime import datetime

app = Flask(__name__)
api = Api(app, version='1.0', title='IMEI API',
    description='API for retrieving IMEI information from Android devices')

ns = api.namespace('imei', description='IMEI operations')

imei_model = api.model('IMEI', {
    'imei1': fields.String(required=True, description='Primary IMEI number'),
    'imei2': fields.String(required=False, description='Secondary IMEI number (dual SIM devices)')
})

@ns.route('')
class IMEIResource(Resource):
    @ns.expect(imei_model)
    @ns.response(200, 'Success')
    def post(self):
        """Submit IMEI information from Android device"""
        data = request.json
        timestamp = datetime.now().isoformat()
        
        # Store in database with timestamp as key
        db[timestamp] = {
            'imei1': data.get('imei1'),
            'imei2': data.get('imei2')
        }
        
        return {
            'message': 'IMEI information received successfully',
            'status': 'success',
            'data': {
                'imei1': data.get('imei1'),
                'imei2': data.get('imei2'),
                'timestamp': timestamp
            }
        }
        
    def get(self):
        """Get all stored IMEI submissions"""
        submissions = {key: db[key] for key in db.keys()}
        return {
            'submissions': submissions
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
