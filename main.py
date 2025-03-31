from flask import Flask, request, send_from_directory
from flask_restx import Api, Resource, fields
import os
from typing import Optional
from replit import db
from datetime import datetime

app = Flask(__name__, static_url_path='/static')
api = Api(app, version='1.0', title='IMEI API',
    description='Get android phone IMEI API with telephony permissions for eSIM activation')

ns = api.namespace('imei', description='IMEI operations')

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
        print("Current database keys:", list(db.keys()))
        submissions = {key: db[key] for key in db.keys()}

        # Collect unique IMEIs
        unique_imei1 = set()
        unique_imei2 = set()

        for submission in submissions.values():
            if submission.get('imei1'):
                unique_imei1.add(submission['imei1'])
            if submission.get('imei2'):
                unique_imei2.add(submission['imei2'])

        stats = {
            'total_submissions': len(submissions),
            'unique_primary_imeis': len(unique_imei1),
            'unique_secondary_imeis': len(unique_imei2),
            'total_unique_imeis': len(unique_imei1.union(unique_imei2))
        }

        return {
            'statistics': stats,
            'submissions': submissions
        }

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)