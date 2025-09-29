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
        """Get products from Shopify to display in marketplace"""
        try:
            if not shopify_service:
                return {'success': False, 'error': 'Shopify service not available'}
            
            # Get products from Shopify via the client
            products_response = shopify_service.client.get_products(limit=limit)
            
            if not products_response.get('success'):
                return {'success': False, 'error': 'Failed to fetch products from Shopify'}
            
            products = products_response.get('products', [])
            marketplace_products = []
            
            for product in products:
                # Transform Shopify product to marketplace format
                marketplace_product = self._transform_shopify_product(product)
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
    
    def create_stripe_checkout_session(self, product_data: Dict, buyer_email: str = None) -> Dict:
        """Create Stripe checkout session for a Shopify product"""
        try:
            if not self.stripe_api_key:
                return {'success': False, 'error': 'Stripe not configured'}
            
            # Create line items for checkout
            line_items = [{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_data['title'],
                        'description': product_data.get('description', ''),
                        'images': product_data.get('images', [])[:1],  # Stripe allows max 8 images
                        'metadata': {
                            'shopify_product_id': str(product_data['id']),
                            'shopify_variant_id': str(product_data.get('variant_id', '')),
                            'sku': product_data.get('sku', ''),
                            'product_type': product_data.get('product_type', ''),
                            'is_marketplace_item': str(product_data.get('is_marketplace_item', False))
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
                    'shopify_product_id': str(product_data['id']),
                    'shopify_variant_id': str(product_data.get('variant_id', '')),
                    'source': 'shopify_marketplace'
                }
            }
            
            # Add customer email if provided
            if buyer_email:
                session_params['customer_email'] = buyer_email
            
            # Enable shipping for physical products
            if product_data.get('product_type', '').lower() in ['smartphone', 'tablet', 'laptop', 'physical']:
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
        """Handle completed Stripe checkout for Shopify product"""
        try:
            if not self.stripe_api_key:
                return {'success': False, 'error': 'Stripe not configured'}
            
            # Retrieve the checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status != 'paid':
                return {'success': False, 'error': 'Payment not completed'}
            
            # Get metadata
            shopify_product_id = session.metadata.get('shopify_product_id')
            shopify_variant_id = session.metadata.get('shopify_variant_id')
            
            # Create order in Shopify (optional - for order management)
            order_data = {
                'line_items': [
                    {
                        'variant_id': shopify_variant_id,
                        'quantity': 1
                    }
                ],
                'customer': {
                    'email': session.customer_details.get('email') if session.customer_details else None
                },
                'financial_status': 'paid',
                'fulfillment_status': 'unfulfilled',
                'note': f'Order paid via Stripe session: {session_id}'
            }
            
            # Add shipping address if available
            if session.shipping_details:
                order_data['shipping_address'] = {
                    'first_name': session.shipping_details.get('name', '').split(' ')[0] if session.shipping_details.get('name') else '',
                    'last_name': ' '.join(session.shipping_details.get('name', '').split(' ')[1:]) if session.shipping_details.get('name') else '',
                    'address1': session.shipping_details.get('address', {}).get('line1', ''),
                    'address2': session.shipping_details.get('address', {}).get('line2', ''),
                    'city': session.shipping_details.get('address', {}).get('city', ''),
                    'province': session.shipping_details.get('address', {}).get('state', ''),
                    'zip': session.shipping_details.get('address', {}).get('postal_code', ''),
                    'country': session.shipping_details.get('address', {}).get('country', '')
                }
            
            # Create order in Shopify
            order_response = shopify_service.client.create_order(order_data)
            
            # Store the completed purchase
            purchase_data = {
                'stripe_session_id': session_id,
                'stripe_payment_intent_id': session.payment_intent,
                'shopify_product_id': shopify_product_id,
                'shopify_variant_id': shopify_variant_id,
                'shopify_order_id': order_response.get('order', {}).get('id') if order_response.get('success') else None,
                'amount_cents': session.amount_total,
                'customer_email': session.customer_details.get('email') if session.customer_details else None,
                'status': 'completed'
            }
            
            # Store in database if marketplace item
            if shopify_service and session.metadata.get('source') == 'shopify_marketplace':
                self._record_marketplace_purchase(purchase_data)
            
            return {
                'success': True,
                'order_id': order_response.get('order', {}).get('id') if order_response.get('success') else None,
                'purchase_data': purchase_data
            }
            
        except Exception as e:
            logger.error(f"Error handling Stripe checkout completion: {e}")
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