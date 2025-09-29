"""
Shopify + Stripe Integration for GORSE Marketplace
Handles product display via Shopify but processes payments through Stripe
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import stripe
from shopify_service import shopify_service

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ShopifyStripeIntegration:
    """Handles integration between Shopify product catalog and Stripe payments"""
    
    def __init__(self):
        self.stripe_api_key = os.environ.get('STRIPE_SECRET_KEY')
        if self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
    
    def get_marketplace_products(self, category: str = None, limit: int = 20) -> Dict:
        """Get approved seller listings for marketplace display"""
        try:
            if not shopify_service:
                return {'success': False, 'error': 'Shopify service not available'}
            
            # Get approved local listings first (these drive what's displayed)
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT sl.*, s.display_name as seller_name, s.rating_average, s.total_sales
                        FROM seller_listings sl
                        JOIN sellers s ON sl.seller_firebase_uid = s.firebase_uid
                        WHERE sl.approval_status = 'approved' 
                        AND sl.is_active = TRUE
                        AND (sl.auction_status IN ('active', 'pending') OR sl.listing_type = 'fixed_price')
                        ORDER BY sl.created_at DESC
                        LIMIT %s
                    """
                    cur.execute(query, (limit,))
                    listings = cur.fetchall()
            
            marketplace_products = []
            for listing in listings:
                # Transform local listing to marketplace product format
                marketplace_product = self._transform_listing_to_product(listing)
                if marketplace_product:
                    marketplace_products.append(marketplace_product)
            
            return {
                'success': True,
                'products': marketplace_products,
                'total': len(marketplace_products)
            }
            
        except Exception as e:
            logger.error(f"Error fetching marketplace products: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_listing_by_id(self, listing_id: int) -> Dict:
        """Get a specific listing by ID for checkout/bidding"""
        try:
            if not shopify_service:
                return {'success': False, 'error': 'Shopify service not available'}
            
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT sl.*, s.display_name as seller_name, s.rating_average, s.total_sales
                        FROM seller_listings sl
                        JOIN sellers s ON sl.seller_firebase_uid = s.firebase_uid
                        WHERE sl.id = %s AND sl.approval_status = 'approved' AND sl.is_active = TRUE
                    """
                    cur.execute(query, (listing_id,))
                    listing_row = cur.fetchone()
                    
                    if not listing_row:
                        return {'success': False, 'error': 'Listing not found or not available'}
                    
                    # Transform to product format
                    listing_product = self._transform_listing_to_product(listing_row)
                    if not listing_product:
                        return {'success': False, 'error': 'Failed to process listing data'}
                    
                    # Add seller UID to product data
                    listing_product['seller_uid'] = listing_row[1]  # seller_firebase_uid
                    
                    return {
                        'success': True,
                        'listing': listing_product
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching listing by ID: {e}")
            return {'success': False, 'error': str(e)}
    
    def _transform_listing_to_product(self, listing_row) -> Optional[Dict]:
        """Transform local seller listing to marketplace product format"""
        try:
            # Convert database row to dict if needed
            if hasattr(listing_row, '_asdict'):
                listing = listing_row._asdict()
            else:
                # Assuming it's already a dict from cursor
                columns = ['id', 'seller_firebase_uid', 'seller_email', 'device_type', 'brand', 'model', 
                          'storage_capacity', 'color', 'condition_grade', 'cosmetic_condition', 
                          'functional_condition', 'original_accessories', 'asking_price_cents', 
                          'minimum_price_cents', 'listing_type', 'photos', 'description', 'imei', 
                          'serial_number', 'carrier_lock_status', 'battery_health', 'approval_status', 
                          'rejection_reason', 'approved_by_admin_uid', 'approved_at', 'shopify_product_id', 
                          'is_active', 'auction_start_time', 'auction_end_time', 'current_bid_cents', 
                          'bid_increment_cents', 'total_bids', 'auction_status', 'winning_bidder_uid', 
                          'winner_selected_at', 'created_at', 'updated_at', 'seller_name', 'rating_average', 'total_sales']
                listing = dict(zip(columns, listing_row))
            
            # Determine current price based on listing type
            if listing['listing_type'] == 'auction':
                current_price = max(listing['current_bid_cents'] or 0, listing['minimum_price_cents'] or 0)
                price_label = f"Current Bid: ${current_price / 100:.2f}"
                if listing['total_bids'] == 0:
                    price_label = f"Starting Bid: ${(listing['minimum_price_cents'] or 0) / 100:.2f}"
            else:
                current_price = listing['asking_price_cents']
                price_label = f"${current_price / 100:.2f}"
            
            # Calculate time remaining for auctions
            time_remaining = None
            if listing['listing_type'] == 'auction' and listing['auction_end_time']:
                from datetime import datetime
                time_left = listing['auction_end_time'] - datetime.now()
                if time_left.total_seconds() > 0:
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    time_remaining = f"{hours}h {minutes}m left"
                else:
                    time_remaining = "Auction ended"
            
            # Build title with device details
            title_parts = [listing['brand'], listing['model']]
            if listing['storage_capacity']:
                title_parts.append(listing['storage_capacity'])
            if listing['color']:
                title_parts.append(listing['color'])
            title = ' '.join(filter(None, title_parts))
            
            return {
                'id': listing['id'],
                'listing_id': listing['id'],
                'title': title,
                'description': listing['description'] or f"{listing['condition_grade'].title()} condition device",
                'price_cents': current_price,
                'price_display': price_label,
                'device_type': listing['device_type'],
                'brand': listing['brand'],
                'model': listing['model'],
                'condition': listing['condition_grade'],
                'photos': listing['photos'] or [],
                'seller_name': listing['seller_name'] or 'Anonymous Seller',
                'seller_rating': float(listing['rating_average'] or 0.0),
                'seller_sales': listing['total_sales'] or 0,
                'listing_type': listing['listing_type'],
                'auction_status': listing['auction_status'],
                'current_bid_cents': listing['current_bid_cents'] or 0,
                'minimum_bid_cents': (listing['current_bid_cents'] or 0) + (listing['bid_increment_cents'] or 500),
                'total_bids': listing['total_bids'] or 0,
                'time_remaining': time_remaining,
                'battery_health': listing['battery_health'],
                'carrier_status': listing['carrier_lock_status'],
                'original_accessories': listing['original_accessories'],
                'shopify_product_id': listing['shopify_product_id'],
                'created_at': listing['created_at'].isoformat() if listing['created_at'] else None,
                'is_marketplace_item': True
            }
            
        except Exception as e:
            logger.error(f"Error transforming listing to product: {e}")
            return None
    
    def _transform_shopify_product(self, shopify_product: Dict) -> Optional[Dict]:
        """Transform Shopify product to marketplace display format"""
        try:
            # Get the first variant for pricing
            variants = shopify_product.get('variants', [])
            if not variants:
                return None
            
            primary_variant = variants[0]
            price_cents = int(float(primary_variant.get('price', 0)) * 100)
            
            # Extract metadata and tags
            tags = shopify_product.get('tags', '').split(',')
            product_type = shopify_product.get('product_type', 'Unknown')
            vendor = shopify_product.get('vendor', 'GORSE Marketplace')
            
            # Get images
            images = shopify_product.get('images', [])
            image_urls = [img.get('src') for img in images if img.get('src')]
            
            # Check if this is a marketplace listing (has pre-owned tag)
            is_marketplace_item = 'pre-owned' in [tag.strip().lower() for tag in tags]
            condition = 'unknown'
            
            for tag in tags:
                tag = tag.strip().lower()
                if tag in ['excellent', 'good', 'fair', 'poor']:
                    condition = tag
                    break
            
            return {
                'id': shopify_product.get('id'),
                'title': shopify_product.get('title'),
                'description': shopify_product.get('body_html', ''),
                'price_cents': price_cents,
                'price_display': f"${price_cents / 100:.2f}",
                'images': image_urls,
                'product_type': product_type,
                'vendor': vendor,
                'condition': condition,
                'is_marketplace_item': is_marketplace_item,
                'tags': [tag.strip() for tag in tags],
                'inventory_quantity': primary_variant.get('inventory_quantity', 0),
                'variant_id': primary_variant.get('id'),
                'sku': primary_variant.get('sku', ''),
                'created_at': shopify_product.get('created_at'),
                'updated_at': shopify_product.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Error transforming Shopify product: {e}")
            return None
    
    def place_auction_bid(self, listing_id: int, bid_amount_cents: int, bidder_uid: str, bidder_email: str) -> Dict:
        """Place a bid on an auction listing"""
        try:
            if not shopify_service:
                return {'success': False, 'error': 'Service not available'}
            
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get current listing details
                    cur.execute("""
                        SELECT * FROM seller_listings 
                        WHERE id = %s AND listing_type = 'auction' AND auction_status = 'active'
                    """, (listing_id,))
                    listing = cur.fetchone()
                    
                    if not listing:
                        return {'success': False, 'error': 'Auction not found or not active'}
                    
                    # Check if auction has ended
                    from datetime import datetime
                    if listing[23] and listing[23] < datetime.now():  # auction_end_time
                        return {'success': False, 'error': 'Auction has ended'}
                    
                    # Validate bid amount
                    current_bid = listing[24] or 0  # current_bid_cents
                    minimum_bid = listing[13] or 0  # minimum_price_cents
                    increment = listing[25] or 500  # bid_increment_cents
                    
                    required_bid = max(current_bid + increment, minimum_bid)
                    if bid_amount_cents < required_bid:
                        return {'success': False, 'error': f'Bid must be at least ${required_bid / 100:.2f}'}
                    
                    # Record the bid
                    cur.execute("""
                        INSERT INTO auction_bids (listing_id, bidder_firebase_uid, bidder_email, bid_amount_cents)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (listing_id, bidder_uid, bidder_email, bid_amount_cents))
                    bid_id = cur.fetchone()[0]
                    
                    # Update previous winning bid
                    cur.execute("""
                        UPDATE auction_bids SET is_winning_bid = FALSE 
                        WHERE listing_id = %s AND is_winning_bid = TRUE
                    """, (listing_id,))
                    
                    # Mark this bid as winning
                    cur.execute("""
                        UPDATE auction_bids SET is_winning_bid = TRUE WHERE id = %s
                    """, (bid_id,))
                    
                    # Update listing with new bid info
                    cur.execute("""
                        UPDATE seller_listings 
                        SET current_bid_cents = %s, total_bids = total_bids + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (bid_amount_cents, listing_id))
                    
                    conn.commit()
                    
                    return {
                        'success': True,
                        'bid_id': bid_id,
                        'bid_amount_cents': bid_amount_cents,
                        'is_winning_bid': True
                    }
                    
        except Exception as e:
            logger.error(f"Error placing auction bid: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_stripe_checkout_session(self, product_data: Dict, buyer_email: str = None, buyer_uid: str = None) -> Dict:
        """Create Stripe checkout session for a marketplace listing"""
        try:
            if not self.stripe_api_key:
                return {'success': False, 'error': 'Stripe not configured'}
            
            # For auction items, verify the buyer is the winning bidder
            if product_data.get('listing_type') == 'auction':
                if not buyer_uid:
                    return {'success': False, 'error': 'Authentication required for auction purchases'}
                
                # Get the winning bidder for this listing
                with shopify_service.get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT bidder_firebase_uid FROM auction_bids 
                            WHERE listing_id = %s AND is_winning_bid = TRUE
                        """, (product_data['listing_id'],))
                        winner = cur.fetchone()
                        
                        if not winner or winner[0] != buyer_uid:
                            return {'success': False, 'error': 'Only the winning bidder can purchase this item'}
            
            # Create line items for checkout
            line_items = [{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_data['title'],
                        'description': product_data.get('description', ''),
                        'images': product_data.get('photos', [])[:1] if product_data.get('photos') else [],
                        'metadata': {
                            'listing_id': str(product_data['listing_id']),
                            'listing_type': product_data.get('listing_type', ''),
                            'seller_uid': product_data.get('seller_uid', ''),
                            'device_type': product_data.get('device_type', ''),
                            'is_marketplace_item': 'true'
                        }
                    },
                    'unit_amount': product_data['price_cents'],
                },
                'quantity': 1,
            }]
            
            # Create checkout session
            session_params = {
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'payment',
                'success_url': f"{os.environ.get('REPLIT_URL', 'http://localhost:5000')}/marketplace/purchase-success?session_id={{CHECKOUT_SESSION_ID}}",
                'cancel_url': f"{os.environ.get('REPLIT_URL', 'http://localhost:5000')}/marketplace?cancelled=true",
                'metadata': {
                    'listing_id': str(product_data['listing_id']),
                    'listing_type': product_data.get('listing_type', ''),
                    'seller_uid': product_data.get('seller_uid', ''),
                    'buyer_uid': buyer_uid or '',
                    'source': 'marketplace_listing'
                }
            }
            
            # Add customer email if provided
            if buyer_email:
                session_params['customer_email'] = buyer_email
            
            # Enable shipping for physical devices
            if product_data.get('device_type', '').lower() in ['smartphone', 'tablet', 'laptop']:
                session_params['shipping_address_collection'] = {
                    'allowed_countries': ['US', 'CA', 'GB', 'AU', 'DE', 'FR', 'ES', 'IT', 'NL']
                }
            
            checkout_session = stripe.checkout.Session.create(**session_params)
            
            return {
                'success': True,
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            }
            
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_stripe_checkout_completion(self, session_id: str) -> Dict:
        """Handle completed Stripe checkout for marketplace listing"""
        try:
            if not self.stripe_api_key:
                return {'success': False, 'error': 'Stripe not configured'}
            
            # Retrieve the checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status != 'paid':
                return {'success': False, 'error': 'Payment not completed'}
            
            # Get metadata
            listing_id = session.metadata.get('listing_id')
            listing_type = session.metadata.get('listing_type')
            seller_uid = session.metadata.get('seller_uid')
            buyer_uid = session.metadata.get('buyer_uid')
            
            if not listing_id:
                return {'success': False, 'error': 'Invalid purchase - missing listing information'}
            
            # Record the marketplace order
            order_data = self._record_marketplace_order(
                listing_id=int(listing_id),
                buyer_uid=buyer_uid,
                buyer_email=session.customer_details.get('email') if session.customer_details else None,
                seller_uid=seller_uid,
                stripe_session_id=session_id,
                stripe_payment_intent_id=session.payment_intent,
                total_amount_cents=session.amount_total,
                shipping_address=session.shipping_details
            )
            
            if not order_data.get('success'):
                return order_data
            
            return {
                'success': True,
                'order_id': order_data.get('order_number'),
                'marketplace_order_id': order_data.get('order_id'),
                'purchase_data': {
                    'listing_id': listing_id,
                    'listing_type': listing_type,
                    'total_amount_cents': session.amount_total,
                    'order_number': order_data.get('order_number')
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling Stripe checkout completion: {e}")
            return {'success': False, 'error': str(e)}
    
    def _record_marketplace_order(self, listing_id: int, buyer_uid: str, buyer_email: str, 
                                  seller_uid: str, stripe_session_id: str, stripe_payment_intent_id: str,
                                  total_amount_cents: int, shipping_address=None) -> Dict:
        """Record marketplace order with seller attribution and commission calculation"""
        try:
            if not shopify_service:
                return {'success': False, 'error': 'Service not available'}
            
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get seller commission rate
                    cur.execute("SELECT commission_rate FROM sellers WHERE firebase_uid = %s", (seller_uid,))
                    seller_data = cur.fetchone()
                    commission_rate = float(seller_data[0]) if seller_data else 0.10  # 10% default
                    
                    # Calculate amounts
                    commission_amount_cents = int(total_amount_cents * commission_rate)
                    seller_amount_cents = total_amount_cents - commission_amount_cents
                    
                    # Generate unique order number
                    import uuid
                    order_number = f"MP-{uuid.uuid4().hex[:8].upper()}"
                    
                    # Create marketplace order
                    cur.execute("""
                        INSERT INTO marketplace_orders (
                            order_number, buyer_firebase_uid, buyer_email, seller_firebase_uid,
                            seller_listing_id, stripe_payment_intent_id, total_amount_cents,
                            seller_amount_cents, commission_amount_cents, order_status,
                            payment_status, shipping_address, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        order_number, buyer_uid, buyer_email, seller_uid, listing_id,
                        stripe_payment_intent_id, total_amount_cents, seller_amount_cents,
                        commission_amount_cents, 'paid', 'paid',
                        json.dumps(shipping_address.__dict__ if shipping_address else {}),
                        datetime.now()
                    ))
                    order_id = cur.fetchone()[0]
                    
                    # Update listing status
                    cur.execute("""
                        UPDATE seller_listings 
                        SET auction_status = 'sold', is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (listing_id,))
                    
                    # Update seller stats
                    cur.execute("""
                        UPDATE sellers 
                        SET total_sales = total_sales + 1, 
                            total_earnings_cents = total_earnings_cents + %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE firebase_uid = %s
                    """, (seller_amount_cents, seller_uid))
                    
                    conn.commit()
                    
                    logger.info(f"Recorded marketplace order: {order_number}")
                    
                    return {
                        'success': True,
                        'order_id': order_id,
                        'order_number': order_number,
                        'seller_amount_cents': seller_amount_cents,
                        'commission_amount_cents': commission_amount_cents
                    }
                    
        except Exception as e:
            logger.error(f"Error recording marketplace order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _record_marketplace_purchase(self, purchase_data: Dict):
        """Record marketplace purchase in database"""
        try:
            if not shopify_service:
                return
            
            with shopify_service.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO marketplace_purchases (
                            stripe_session_id, stripe_payment_intent_id, 
                            shopify_product_id, shopify_variant_id, shopify_order_id,
                            amount_cents, customer_email, purchase_status, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        purchase_data['stripe_session_id'],
                        purchase_data['stripe_payment_intent_id'],
                        purchase_data['shopify_product_id'],
                        purchase_data['shopify_variant_id'],
                        purchase_data['shopify_order_id'],
                        purchase_data['amount_cents'],
                        purchase_data['customer_email'],
                        purchase_data['status'],
                        datetime.now()
                    ))
                    conn.commit()
            
            logger.info(f"Recorded marketplace purchase: {purchase_data['stripe_session_id']}")
            
        except Exception as e:
            logger.error(f"Error recording marketplace purchase: {e}")

# Global integration instance
shopify_stripe_integration = ShopifyStripeIntegration()