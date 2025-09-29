import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from shopify_client import shopify_client

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ShopifyService:
    """Service layer for Shopify marketplace integration"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.client = shopify_client
        logger.info("ShopifyService initialized with database pool")
    
    @contextmanager
    def get_db_connection(self):
        connection = self.db_pool.getconn()
        try:
            yield connection
        finally:
            self.db_pool.putconn(connection)
    
    # Shop Management
    def setup_shop(self, shop_domain: str, access_token: str, shop_data: Dict = None) -> Dict:
        """Setup and store Shopify shop credentials"""
        try:
            # Set credentials in client
            self.client.set_credentials(shop_domain, access_token)
            
            # Store in database
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO shopify_shops (shop_domain, access_token, shop_name, email, plan_name)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (shop_domain) 
                        DO UPDATE SET 
                            access_token = EXCLUDED.access_token,
                            shop_name = EXCLUDED.shop_name,
                            email = EXCLUDED.email,
                            plan_name = EXCLUDED.plan_name,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (
                        shop_domain,
                        access_token,
                        shop_data.get('name') if shop_data else None,
                        shop_data.get('email') if shop_data else None,
                        shop_data.get('plan_name') if shop_data else None
                    ))
                    shop_id = cur.fetchone()[0]
                    conn.commit()
            
            # Setup initial collections for marketplace categories
            self._setup_marketplace_collections(shop_domain)
            
            # Setup webhooks
            self._setup_webhooks(shop_domain)
            
            logger.info(f"Successfully setup shop: {shop_domain}")
            return {'success': True, 'shop_id': shop_id}
            
        except Exception as e:
            logger.error(f"Error setting up shop {shop_domain}: {e}")
            raise
    
    def _setup_marketplace_collections(self, shop_domain: str):
        """Create Shopify collections for marketplace categories"""
        collections_to_create = [
            {
                'title': 'Device Trade-ins',
                'handle': 'device-trade-ins',
                'collection_type': 'devices',
                'body_html': 'Pre-owned devices available for purchase'
            },
            {
                'title': 'eSIM Services',
                'handle': 'esim-services',
                'collection_type': 'esim_services',
                'body_html': 'Global connectivity and eSIM activation services'
            },
            {
                'title': 'Physical Products',
                'handle': 'physical-products',
                'collection_type': 'physical_products',
                'body_html': 'Hardware and collectibles'
            }
        ]
        
        for collection_data in collections_to_create:
            try:
                # Create collection in Shopify
                result = self.client.create_collection(collection_data)
                shopify_collection = result.get('custom_collection', {})
                
                # Store in database
                with self.get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO shopify_collections 
                            (shopify_collection_id, shop_domain, collection_title, collection_handle, collection_type)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (shopify_collection_id, shop_domain) DO NOTHING
                        """, (
                            shopify_collection.get('id'),
                            shop_domain,
                            shopify_collection.get('title'),
                            shopify_collection.get('handle'),
                            collection_data['collection_type']
                        ))
                        conn.commit()
                
                logger.info(f"Created collection: {collection_data['title']}")
                
            except Exception as e:
                logger.error(f"Error creating collection {collection_data['title']}: {e}")
    
    def _setup_webhooks(self, shop_domain: str):
        """Setup webhooks for Shopify events"""
        # Get the base URL for webhook endpoints
        base_url = os.environ.get('REPLIT_URL', 'https://localhost:5000')
        
        webhooks_to_create = [
            ('orders/create', f'{base_url}/api/shopify/webhook/order/created'),
            ('orders/updated', f'{base_url}/api/shopify/webhook/order/updated'),
            ('orders/paid', f'{base_url}/api/shopify/webhook/order/paid'),
            ('products/create', f'{base_url}/api/shopify/webhook/product/created'),
            ('products/update', f'{base_url}/api/shopify/webhook/product/updated'),
        ]
        
        for topic, address in webhooks_to_create:
            try:
                self.client.create_webhook(topic, address)
                logger.info(f"Created webhook for {topic}")
            except Exception as e:
                logger.error(f"Error creating webhook for {topic}: {e}")
    
    # Seller Management
    def create_seller_profile(self, firebase_uid: str, email: str, display_name: str = None) -> Dict:
        """Create a new seller profile"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO sellers (firebase_uid, email, display_name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (firebase_uid) 
                        DO UPDATE SET 
                            email = EXCLUDED.email,
                            display_name = EXCLUDED.display_name,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (firebase_uid, email, display_name))
                    seller_id = cur.fetchone()[0]
                    conn.commit()
            
            logger.info(f"Created seller profile for: {email}")
            return {'success': True, 'seller_id': seller_id}
            
        except Exception as e:
            logger.error(f"Error creating seller profile: {e}")
            raise
    
    def get_seller_profile(self, firebase_uid: str) -> Optional[Dict]:
        """Get seller profile by Firebase UID"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, firebase_uid, email, display_name, verification_status,
                               rating_average, total_sales, total_earnings_cents, is_active,
                               created_at, updated_at
                        FROM sellers 
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))
                    row = cur.fetchone()
                    
                    if row:
                        return {
                            'id': row[0],
                            'firebase_uid': row[1],
                            'email': row[2],
                            'display_name': row[3],
                            'verification_status': row[4],
                            'rating_average': float(row[5]) if row[5] else 0.0,
                            'total_sales': row[6],
                            'total_earnings_cents': row[7],
                            'is_active': row[8],
                            'created_at': row[9],
                            'updated_at': row[10]
                        }
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting seller profile: {e}")
            raise
    
    # Listing Management
    def create_device_listing(self, listing_data: Dict) -> Dict:
        """Create a new device listing for seller"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO seller_listings (
                            seller_firebase_uid, seller_email, device_type, brand, model,
                            storage_capacity, color, condition_grade, cosmetic_condition,
                            functional_condition, original_accessories, asking_price_cents,
                            minimum_price_cents, listing_type, photos, description,
                            imei, serial_number, carrier_lock_status, battery_health
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                    """, (
                        listing_data['seller_firebase_uid'],
                        listing_data['seller_email'],
                        listing_data['device_type'],
                        listing_data.get('brand'),
                        listing_data['model'],
                        listing_data.get('storage_capacity'),
                        listing_data.get('color'),
                        listing_data['condition_grade'],
                        listing_data.get('cosmetic_condition'),
                        listing_data.get('functional_condition'),
                        json.dumps(listing_data.get('original_accessories', [])),
                        listing_data['asking_price_cents'],
                        listing_data.get('minimum_price_cents'),
                        listing_data.get('listing_type', 'auction'),
                        json.dumps(listing_data.get('photos', [])),
                        listing_data.get('description'),
                        listing_data.get('imei'),
                        listing_data.get('serial_number'),
                        listing_data.get('carrier_lock_status'),
                        listing_data.get('battery_health')
                    ))
                    listing_id = cur.fetchone()[0]
                    conn.commit()
            
            logger.info(f"Created device listing: {listing_id}")
            return {'success': True, 'listing_id': listing_id}
            
        except Exception as e:
            logger.error(f"Error creating device listing: {e}")
            raise
    
    def approve_listing(self, listing_id: int, admin_uid: str) -> Dict:
        """Approve a seller listing and sync to Shopify"""
        try:
            # Get listing details
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT seller_firebase_uid, device_type, brand, model, condition_grade,
                               asking_price_cents, description, photos
                        FROM seller_listings 
                        WHERE id = %s AND approval_status = 'pending'
                    """, (listing_id,))
                    listing = cur.fetchone()
                    
                    if not listing:
                        raise ValueError("Listing not found or already processed")
            
            # Create product in Shopify
            product_title = f"{listing[2]} {listing[3]} ({listing[4]} condition)"
            product_data = {
                'title': product_title,
                'body_html': listing[6] or f"Pre-owned {listing[1]} in {listing[4]} condition",
                'vendor': 'GORSE Marketplace',
                'product_type': listing[1],
                'tags': f"pre-owned,{listing[1]},{listing[4]},marketplace",
                'variants': [{
                    'price': str(listing[5] / 100),  # Convert cents to dollars
                    'inventory_quantity': 1,
                    'inventory_management': 'shopify'
                }]
            }
            
            # Add images if available
            photos = json.loads(listing[7]) if listing[7] else []
            if photos:
                product_data['images'] = [{'src': photo} for photo in photos]
            
            # Create product in Shopify
            result = self.client.create_product(product_data)
            shopify_product = result.get('product', {})
            
            # Update listing with approval and Shopify product ID
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE seller_listings 
                        SET approval_status = 'approved',
                            approved_by_admin_uid = %s,
                            approved_at = CURRENT_TIMESTAMP,
                            shopify_product_id = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (admin_uid, shopify_product.get('id'), listing_id))
                    
                    # Create sync record
                    cur.execute("""
                        INSERT INTO shopify_products (
                            local_product_id, shopify_product_id, shop_domain,
                            product_title, sku, price_cents, sync_status, last_sync_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        listing_id,
                        shopify_product.get('id'),
                        self.client.shop_domain,
                        product_title,
                        f"LISTING-{listing_id}",
                        listing[5],
                        'synced',
                        datetime.now()
                    ))
                    conn.commit()
            
            # Add to appropriate collection
            device_collection_id = self._get_collection_id('devices')
            if device_collection_id:
                self.client.add_product_to_collection(device_collection_id, shopify_product.get('id'))
            
            logger.info(f"Approved listing {listing_id} and synced to Shopify")
            return {'success': True, 'shopify_product_id': shopify_product.get('id')}
            
        except Exception as e:
            logger.error(f"Error approving listing {listing_id}: {e}")
            raise
    
    def _get_collection_id(self, collection_type: str) -> Optional[str]:
        """Get Shopify collection ID by type"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT shopify_collection_id 
                        FROM shopify_collections 
                        WHERE collection_type = %s AND is_active = TRUE
                        LIMIT 1
                    """, (collection_type,))
                    row = cur.fetchone()
                    return str(row[0]) if row else None
        except Exception as e:
            logger.error(f"Error getting collection ID: {e}")
            return None
    
    # Order Management
    def create_marketplace_order(self, order_data: Dict) -> Dict:
        """Create a marketplace order from Shopify purchase"""
        try:
            # Calculate commission
            total_amount = order_data['total_amount_cents']
            commission_rate = order_data.get('commission_rate', 0.10)  # 10% default
            commission_amount = int(total_amount * commission_rate)
            seller_amount = total_amount - commission_amount
            
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO marketplace_orders (
                            order_number, buyer_firebase_uid, buyer_email,
                            seller_firebase_uid, seller_listing_id, shopify_order_id,
                            stripe_payment_intent_id, total_amount_cents,
                            seller_amount_cents, commission_amount_cents,
                            shipping_address
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        order_data['order_number'],
                        order_data.get('buyer_firebase_uid'),
                        order_data.get('buyer_email'),
                        order_data['seller_firebase_uid'],
                        order_data['seller_listing_id'],
                        order_data.get('shopify_order_id'),
                        order_data.get('stripe_payment_intent_id'),
                        total_amount,
                        seller_amount,
                        commission_amount,
                        json.dumps(order_data.get('shipping_address', {}))
                    ))
                    order_id = cur.fetchone()[0]
                    conn.commit()
            
            logger.info(f"Created marketplace order: {order_id}")
            return {'success': True, 'order_id': order_id}
            
        except Exception as e:
            logger.error(f"Error creating marketplace order: {e}")
            raise

# Global service instance will be initialized with database pool
shopify_service = None