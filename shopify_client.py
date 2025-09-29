import os
import json
import requests
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ShopifyClient:
    """Shopify Admin API client for marketplace integration"""
    
    def __init__(self):
        self.client_id = os.environ.get('SHOPIFY_CLIENT_ID')
        self.client_secret = os.environ.get('SHOPIFY_SECRET')
        self.shop_domain = None  # Will be set after OAuth
        self.access_token = None  # Will be set after OAuth
        
        if not self.client_id or not self.client_secret:
            logger.error("SHOPIFY_CLIENT_ID and SHOPIFY_SECRET must be configured")
            raise ValueError("Missing Shopify credentials")
    
    def get_oauth_url(self, shop_domain: str, redirect_uri: str, scopes: List[str] = None) -> str:
        """Generate OAuth authorization URL for shop setup"""
        if not scopes:
            scopes = [
                'read_products', 'write_products',
                'read_orders', 'write_orders',
                'read_customers', 'write_customers',
                'read_inventory', 'write_inventory',
                'read_checkouts', 'write_checkouts'
            ]
        
        scope_string = ','.join(scopes)
        oauth_url = (
            f"https://{shop_domain}/admin/oauth/authorize?"
            f"client_id={self.client_id}&"
            f"scope={scope_string}&"
            f"redirect_uri={redirect_uri}"
        )
        
        logger.info(f"Generated OAuth URL for shop: {shop_domain}")
        return oauth_url
    
    def exchange_code_for_token(self, shop_domain: str, code: str) -> str:
        """Exchange authorization code for access token"""
        url = f"https://{shop_domain}/admin/oauth/access_token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                self.shop_domain = shop_domain
                self.access_token = access_token
                logger.info(f"Successfully obtained access token for shop: {shop_domain}")
                return access_token
            else:
                raise ValueError("No access token in response")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    def set_credentials(self, shop_domain: str, access_token: str):
        """Set shop credentials for API calls"""
        self.shop_domain = shop_domain
        self.access_token = access_token
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Make authenticated request to Shopify Admin API"""
        if not self.shop_domain or not self.access_token:
            raise ValueError("Shop domain and access token must be configured")
        
        url = f"https://{self.shop_domain}/admin/api/2023-10/{endpoint}"
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Shopify API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response content: {e.response.text}")
            raise
    
    # Product Management
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Shopify"""
        logger.info(f"Creating product: {product_data.get('title', 'Unknown')}")
        return self._make_request('products.json', 'POST', {'product': product_data})
    
    def get_product(self, product_id: str) -> Dict:
        """Get a specific product by ID"""
        return self._make_request(f'products/{product_id}.json')
    
    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """Update an existing product"""
        logger.info(f"Updating product ID: {product_id}")
        return self._make_request(f'products/{product_id}.json', 'PUT', {'product': product_data})
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        logger.info(f"Deleting product ID: {product_id}")
        self._make_request(f'products/{product_id}.json', 'DELETE')
        return True
    
    def list_products(self, limit: int = 50, page_info: str = None) -> Dict:
        """List products with pagination"""
        endpoint = f'products.json?limit={limit}'
        if page_info:
            endpoint += f'&page_info={page_info}'
        return self._make_request(endpoint)
    
    # Collection Management
    def create_collection(self, collection_data: Dict) -> Dict:
        """Create a custom collection"""
        logger.info(f"Creating collection: {collection_data.get('title', 'Unknown')}")
        return self._make_request('custom_collections.json', 'POST', {'custom_collection': collection_data})
    
    def get_collection(self, collection_id: str) -> Dict:
        """Get a specific collection by ID"""
        return self._make_request(f'custom_collections/{collection_id}.json')
    
    def list_collections(self) -> Dict:
        """List all custom collections"""
        return self._make_request('custom_collections.json')
    
    def add_product_to_collection(self, collection_id: str, product_id: str) -> Dict:
        """Add a product to a collection"""
        collect_data = {
            'collect': {
                'product_id': product_id,
                'collection_id': collection_id
            }
        }
        return self._make_request('collects.json', 'POST', collect_data)
    
    # Order Management
    def get_order(self, order_id: str) -> Dict:
        """Get a specific order by ID"""
        return self._make_request(f'orders/{order_id}.json')
    
    def list_orders(self, status: str = 'any', limit: int = 50) -> Dict:
        """List orders with optional status filter"""
        endpoint = f'orders.json?status={status}&limit={limit}'
        return self._make_request(endpoint)
    
    def update_order(self, order_id: str, order_data: Dict) -> Dict:
        """Update an existing order"""
        return self._make_request(f'orders/{order_id}.json', 'PUT', {'order': order_data})
    
    # Webhook Management
    def create_webhook(self, topic: str, address: str) -> Dict:
        """Create a webhook for Shopify events"""
        webhook_data = {
            'webhook': {
                'topic': topic,
                'address': address,
                'format': 'json'
            }
        }
        logger.info(f"Creating webhook for topic: {topic}")
        return self._make_request('webhooks.json', 'POST', webhook_data)
    
    def list_webhooks(self) -> Dict:
        """List all configured webhooks"""
        return self._make_request('webhooks.json')
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        logger.info(f"Deleting webhook ID: {webhook_id}")
        self._make_request(f'webhooks/{webhook_id}.json', 'DELETE')
        return True
    
    # Inventory Management
    def get_inventory_levels(self, inventory_item_ids: List[str] = None, location_ids: List[str] = None) -> Dict:
        """Get inventory levels for items and locations"""
        endpoint = 'inventory_levels.json?'
        if inventory_item_ids:
            endpoint += f"inventory_item_ids={','.join(inventory_item_ids)}&"
        if location_ids:
            endpoint += f"location_ids={','.join(location_ids)}&"
        return self._make_request(endpoint.rstrip('&?'))
    
    def update_inventory_level(self, inventory_item_id: str, location_id: str, available: int) -> Dict:
        """Update inventory level for an item at a location"""
        inventory_data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id,
            'available': available
        }
        return self._make_request('inventory_levels/set.json', 'POST', inventory_data)

# Global client instance
shopify_client = ShopifyClient()