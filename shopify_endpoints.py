"""
Shopify API endpoints for marketplace integration
"""
import json
import logging
from flask import request, jsonify
from auth_helpers import require_auth, require_admin_auth
from firebase_helper import firebase_auth_required

logger = logging.getLogger(__name__)

def register_shopify_endpoints(app, shopify_service):
    """Register Shopify API endpoints with the Flask app"""
    
    @app.route('/api/shopify/oauth/url', methods=['POST'])
    @firebase_auth_required
    def get_shopify_oauth_url():
        """Get OAuth URL for Shopify app installation"""
        try:
            data = request.get_json()
            shop_domain = data.get('shop_domain')
            
            if not shop_domain:
                return jsonify({'error': 'shop_domain is required'}), 400
            
            # Remove https:// and .myshopify.com if present
            shop_domain = shop_domain.replace('https://', '').replace('http://', '')
            if not shop_domain.endswith('.myshopify.com'):
                shop_domain += '.myshopify.com'
            
            redirect_uri = f"{request.host_url}api/shopify/oauth/callback"
            oauth_url = shopify_service.client.get_oauth_url(shop_domain, redirect_uri)
            
            return jsonify({
                'success': True,
                'oauth_url': oauth_url,
                'shop_domain': shop_domain
            })
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/shopify/oauth/callback', methods=['GET'])
    def shopify_oauth_callback():
        """Handle OAuth callback from Shopify"""
        try:
            code = request.args.get('code')
            shop = request.args.get('shop')
            
            if not code or not shop:
                return jsonify({'error': 'Missing authorization code or shop parameter'}), 400
            
            # Exchange code for access token
            access_token = shopify_service.client.exchange_code_for_token(shop, code)
            
            # Setup shop in our system
            result = shopify_service.setup_shop(shop, access_token)
            
            return jsonify({
                'success': True,
                'message': f'Successfully connected shop: {shop}',
                'shop_id': result.get('shop_id')
            })
            
        except Exception as e:
            logger.error(f"Error in OAuth callback: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sellers/register', methods=['POST'])
    @firebase_auth_required
    def register_seller():
        """Register a new seller profile"""
        try:
            user_uid = request.user_uid
            user_email = request.user_email
            data = request.get_json()
            
            display_name = data.get('display_name', '')
            
            result = shopify_service.create_seller_profile(
                firebase_uid=user_uid,
                email=user_email,
                display_name=display_name
            )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error registering seller: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sellers/profile', methods=['GET'])
    @firebase_auth_required
    def get_seller_profile():
        """Get current user's seller profile"""
        try:
            user_uid = request.user_uid
            profile = shopify_service.get_seller_profile(user_uid)
            
            if profile:
                return jsonify({'success': True, 'profile': profile})
            else:
                return jsonify({'success': False, 'message': 'Seller profile not found'}), 404
                
        except Exception as e:
            logger.error(f"Error getting seller profile: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/listings/create', methods=['POST'])
    @firebase_auth_required
    def create_device_listing():
        """Create a new device listing"""
        try:
            user_uid = request.user_uid
            user_email = request.user_email
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['device_type', 'model', 'condition_grade', 'asking_price_cents']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Add seller information
            data['seller_firebase_uid'] = user_uid
            data['seller_email'] = user_email
            
            result = shopify_service.create_device_listing(data)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error creating device listing: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/listings/approve/<int:listing_id>', methods=['POST'])
    @require_admin_auth
    def approve_listing(listing_id):
        """Approve a seller listing (admin only)"""
        try:
            admin_uid = request.user_uid
            
            result = shopify_service.approve_listing(listing_id, admin_uid)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error approving listing {listing_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/listings/reject/<int:listing_id>', methods=['POST'])
    @require_admin_auth
    def reject_listing(listing_id):
        """Reject a seller listing (admin only)"""
        try:
            admin_uid = request.user_uid
            data = request.get_json()
            rejection_reason = data.get('reason', 'No reason provided')
            
            # Update listing status
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE seller_listings 
                        SET approval_status = 'rejected',
                            rejection_reason = %s,
                            approved_by_admin_uid = %s,
                            approved_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND approval_status = 'pending'
                    """, (rejection_reason, admin_uid, listing_id))
                    
                    if cur.rowcount == 0:
                        return jsonify({'error': 'Listing not found or already processed'}), 404
                    
                    conn.commit()
            
            return jsonify({'success': True, 'message': 'Listing rejected'})
            
        except Exception as e:
            logger.error(f"Error rejecting listing {listing_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/listings/pending', methods=['GET'])
    @require_admin_auth
    def get_pending_listings():
        """Get all pending listings for admin review"""
        try:
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT l.id, l.seller_email, l.device_type, l.brand, l.model,
                               l.condition_grade, l.asking_price_cents, l.description,
                               l.photos, l.created_at, s.display_name
                        FROM seller_listings l
                        LEFT JOIN sellers s ON l.seller_firebase_uid = s.firebase_uid
                        WHERE l.approval_status = 'pending'
                        ORDER BY l.created_at ASC
                    """)
                    
                    listings = []
                    for row in cur.fetchall():
                        listings.append({
                            'id': row[0],
                            'seller_email': row[1],
                            'device_type': row[2],
                            'brand': row[3],
                            'model': row[4],
                            'condition_grade': row[5],
                            'asking_price_cents': row[6],
                            'description': row[7],
                            'photos': json.loads(row[8]) if row[8] else [],
                            'created_at': row[9].isoformat(),
                            'seller_name': row[10]
                        })
            
            return jsonify({'success': True, 'listings': listings})
            
        except Exception as e:
            logger.error(f"Error getting pending listings: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sellers/<seller_uid>/listings', methods=['GET'])
    @firebase_auth_required
    def get_seller_listings(seller_uid):
        """Get listings for a specific seller"""
        try:
            # Check if user can access this seller's listings
            user_uid = request.user_uid
            if user_uid != seller_uid and not request.user_is_admin:
                return jsonify({'error': 'Access denied'}), 403
            
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, device_type, brand, model, condition_grade,
                               asking_price_cents, approval_status, description,
                               photos, shopify_product_id, created_at, updated_at
                        FROM seller_listings
                        WHERE seller_firebase_uid = %s
                        ORDER BY created_at DESC
                    """, (seller_uid,))
                    
                    listings = []
                    for row in cur.fetchall():
                        listings.append({
                            'id': row[0],
                            'device_type': row[1],
                            'brand': row[2],
                            'model': row[3],
                            'condition_grade': row[4],
                            'asking_price_cents': row[5],
                            'approval_status': row[6],
                            'description': row[7],
                            'photos': json.loads(row[8]) if row[8] else [],
                            'shopify_product_id': row[9],
                            'created_at': row[10].isoformat(),
                            'updated_at': row[11].isoformat()
                        })
            
            return jsonify({'success': True, 'listings': listings})
            
        except Exception as e:
            logger.error(f"Error getting seller listings: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Webhook endpoints
    @app.route('/api/shopify/webhook/order/created', methods=['POST'])
    def shopify_order_created():
        """Handle Shopify order created webhook"""
        try:
            data = request.get_json()
            
            # Store webhook event
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO shopify_webhook_events 
                        (event_id, shop_domain, event_type, event_data)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        data.get('id'),
                        request.headers.get('X-Shopify-Shop-Domain'),
                        'orders/create',
                        json.dumps(data)
                    ))
                    conn.commit()
            
            logger.info(f"Processed Shopify order created webhook: {data.get('id')}")
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Error processing order created webhook: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/shopify/webhook/order/paid', methods=['POST'])
    def shopify_order_paid():
        """Handle Shopify order paid webhook"""
        try:
            data = request.get_json()
            
            # Store webhook event
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO shopify_webhook_events 
                        (event_id, shop_domain, event_type, event_data)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        data.get('id'),
                        request.headers.get('X-Shopify-Shop-Domain'),
                        'orders/paid',
                        json.dumps(data)
                    ))
                    conn.commit()
            
            # TODO: Process payment and update marketplace order status
            
            logger.info(f"Processed Shopify order paid webhook: {data.get('id')}")
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Error processing order paid webhook: {e}")
            return jsonify({'error': str(e)}), 500