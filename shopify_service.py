import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class ShopifyService:
    """Service for Shopify API integration"""
    
    def __init__(self):
        self.store_url = os.environ.get('SHOPIFY_STORE_URL', '').strip()
        self.access_token = os.environ.get('SHOPIFY_ACCESS_TOKEN', '').strip()
        self.client_id = os.environ.get('SHOPIFY_CLIENT_ID', '').strip()
        self.client_secret = os.environ.get('SHOPIFY_SECRET', '').strip()
        
        # Ensure store URL is properly formatted
        if self.store_url and not self.store_url.startswith('http'):
            self.store_url = f'https://{self.store_url}'
        
        self.api_version = '2024-01'
        self.base_url = f'{self.store_url}/admin/api/{self.api_version}'
        
        print(f"Shopify Service initialized:")
        print(f"  Store URL: {self.store_url}")
        print(f"  Access Token configured: {bool(self.access_token)}")
        print(f"  Client ID configured: {bool(self.client_id)}")
        print(f"  Client Secret configured: {bool(self.client_secret)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Shopify API connection"""
        try:
            if not self.store_url or not self.access_token:
                return {
                    'success': False,
                    'error': 'Missing Shopify credentials',
                    'details': {
                        'store_url': bool(self.store_url),
                        'access_token': bool(self.access_token)
                    }
                }
            
            response = requests.get(
                f'{self.base_url}/shop.json',
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                return {
                    'success': True,
                    'shop': {
                        'name': shop_data.get('name'),
                        'domain': shop_data.get('domain'),
                        'email': shop_data.get('email'),
                        'currency': shop_data.get('currency'),
                        'timezone': shop_data.get('timezone')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_products(self, limit: int = 50, page_info: Optional[str] = None) -> Dict[str, Any]:
        """Get products from Shopify"""
        try:
            url = f'{self.base_url}/products.json?limit={limit}'
            if page_info:
                url += f'&page_info={page_info}'
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'products': data.get('products', []),
                    'page_info': response.headers.get('Link')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch products: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a single product by ID"""
        try:
            response = requests.get(
                f'{self.base_url}/products/{product_id}.json',
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'product': response.json().get('product')
                }
            else:
                return {
                    'success': False,
                    'error': f'Product not found: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product in Shopify"""
        try:
            response = requests.post(
                f'{self.base_url}/products.json',
                headers=self._get_headers(),
                json={'product': product_data},
                timeout=10
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'product': response.json().get('product')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to create product: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product"""
        try:
            response = requests.put(
                f'{self.base_url}/products/{product_id}.json',
                headers=self._get_headers(),
                json={'product': product_data},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'product': response.json().get('product')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update product: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_inventory(self, inventory_item_id: str, available: int, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Update inventory levels"""
        try:
            # First, get locations if not provided
            if not location_id:
                locations_response = requests.get(
                    f'{self.base_url}/locations.json',
                    headers=self._get_headers(),
                    timeout=10
                )
                if locations_response.status_code == 200:
                    locations = locations_response.json().get('locations', [])
                    if locations:
                        location_id = str(locations[0]['id'])
            
            response = requests.post(
                f'{self.base_url}/inventory_levels/set.json',
                headers=self._get_headers(),
                json={
                    'location_id': location_id,
                    'inventory_item_id': inventory_item_id,
                    'available': available
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'inventory_level': response.json().get('inventory_level')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update inventory: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_orders(self, status: str = 'any', limit: int = 50) -> Dict[str, Any]:
        """Get orders from Shopify"""
        try:
            response = requests.get(
                f'{self.base_url}/orders.json?status={status}&limit={limit}',
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'orders': response.json().get('orders', [])
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch orders: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a single order by ID"""
        try:
            response = requests.get(
                f'{self.base_url}/orders/{order_id}.json',
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'order': response.json().get('order')
                }
            else:
                return {
                    'success': False,
                    'error': f'Order not found: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def fulfill_order(self, order_id: str, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fulfill an order"""
        try:
            response = requests.post(
                f'{self.base_url}/orders/{order_id}/fulfillments.json',
                headers=self._get_headers(),
                json={
                    'fulfillment': {
                        'line_items': line_items,
                        'notify_customer': True
                    }
                },
                timeout=10
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'fulfillment': response.json().get('fulfillment')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fulfill order: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Initialize service
shopify_service = ShopifyService()
