"""
Device Image Service - Provides stock device images based on make and model
"""
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class DeviceImageService:
    """Service for managing device stock images and specifications"""
    
    def __init__(self):
        # Stock device image mappings based on make/model
        self.device_images = {
            'apple': {
                'iphone 15 pro max': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-max-bluetitanium-select?wid=470&hei=556&fmt=png-alpha&.v=1693086369408',
                    'colors': ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium'],
                    'storage_options': ['128GB', '256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 119900, 'good': 109900, 'fair': 99900, 'poor': 89900}
                },
                'iphone 15 pro': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-naturalttanium-select?wid=470&hei=556&fmt=png-alpha&.v=1693086369408',
                    'colors': ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium'],
                    'storage_options': ['128GB', '256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 99900, 'good': 89900, 'fair': 79900, 'poor': 69900}
                },
                'iphone 15': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pink-select-202309?wid=470&hei=556&fmt=png-alpha&.v=1693086369408',
                    'colors': ['Pink', 'Yellow', 'Green', 'Blue', 'Black'],
                    'storage_options': ['128GB', '256GB', '512GB'],
                    'estimated_values': {'excellent': 79900, 'good': 69900, 'fair': 59900, 'poor': 49900}
                },
                'iphone 14 pro max': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-pro-max-deeppurple-select?wid=470&hei=556&fmt=png-alpha&.v=1663703841509',
                    'colors': ['Deep Purple', 'Gold', 'Silver', 'Space Black'],
                    'storage_options': ['128GB', '256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 109900, 'good': 99900, 'fair': 89900, 'poor': 79900}
                },
                'iphone 14 pro': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-pro-deeppurple-select?wid=470&hei=556&fmt=png-alpha&.v=1663703841509',
                    'colors': ['Deep Purple', 'Gold', 'Silver', 'Space Black'],
                    'storage_options': ['128GB', '256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 89900, 'good': 79900, 'fair': 69900, 'poor': 59900}
                },
                'iphone 14': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-blue-select-202209?wid=470&hei=556&fmt=png-alpha&.v=1660753040428',
                    'colors': ['Blue', 'Purple', 'Yellow', 'Midnight', 'Starlight', 'Red'],
                    'storage_options': ['128GB', '256GB', '512GB'],
                    'estimated_values': {'excellent': 69900, 'good': 59900, 'fair': 49900, 'poor': 39900}
                },
                'iphone 13 pro max': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-pro-max-graphite-select?wid=470&hei=556&fmt=png-alpha&.v=1631652954',
                    'colors': ['Graphite', 'Gold', 'Silver', 'Sierra Blue', 'Alpine Green'],
                    'storage_options': ['128GB', '256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 89900, 'good': 79900, 'fair': 69900, 'poor': 59900}
                },
                'iphone 13': {
                    'image_url': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-pink-select-2021?wid=470&hei=556&fmt=png-alpha&.v=1629842709',
                    'colors': ['Pink', 'Blue', 'Midnight', 'Starlight', 'Red'],
                    'storage_options': ['128GB', '256GB', '512GB'],
                    'estimated_values': {'excellent': 59900, 'good': 49900, 'fair': 39900, 'poor': 29900}
                }
            },
            'samsung': {
                'galaxy s24 ultra': {
                    'image_url': 'https://images.samsung.com/is/image/samsung/p6pim/us/2401/gallery/us-galaxy-s24-ultra-s928-sm-s928uzkfxaa-539573279?$650_519_PNG$',
                    'colors': ['Titanium Black', 'Titanium Gray', 'Titanium Violet', 'Titanium Yellow'],
                    'storage_options': ['256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 119900, 'good': 109900, 'fair': 99900, 'poor': 89900}
                },
                'galaxy s24+': {
                    'image_url': 'https://images.samsung.com/is/image/samsung/p6pim/us/2401/gallery/us-galaxy-s24-plus-s926-sm-s926ulbfxaa-539573267?$650_519_PNG$',
                    'colors': ['Onyx Black', 'Marble Gray', 'Cobalt Violet', 'Amber Yellow'],
                    'storage_options': ['256GB', '512GB'],
                    'estimated_values': {'excellent': 99900, 'good': 89900, 'fair': 79900, 'poor': 69900}
                },
                'galaxy s24': {
                    'image_url': 'https://images.samsung.com/is/image/samsung/p6pim/us/2401/gallery/us-galaxy-s24-s921-sm-s921ulbfxaa-539573255?$650_519_PNG$',
                    'colors': ['Onyx Black', 'Marble Gray', 'Cobalt Violet', 'Amber Yellow'],
                    'storage_options': ['128GB', '256GB'],
                    'estimated_values': {'excellent': 79900, 'good': 69900, 'fair': 59900, 'poor': 49900}
                },
                'galaxy s23 ultra': {
                    'image_url': 'https://images.samsung.com/is/image/samsung/p6pim/us/2302/gallery/us-galaxy-s23-ultra-s918-sm-s918uzkfxaa-534859740?$650_519_PNG$',
                    'colors': ['Phantom Black', 'Green', 'Cream', 'Lavender'],
                    'storage_options': ['256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 99900, 'good': 89900, 'fair': 79900, 'poor': 69900}
                }
            },
            'google': {
                'pixel 8 pro': {
                    'image_url': 'https://lh3.googleusercontent.com/7O0fC6G2pKHKikDMJJUfX_F1pQ8pHKOFO2WlhyJ7nOpCLSBHp0U-L0OEG4J1Dp7s2R-gvESpYR_QYg=rw-e365-w1800',
                    'colors': ['Obsidian', 'Porcelain', 'Bay'],
                    'storage_options': ['128GB', '256GB', '512GB', '1TB'],
                    'estimated_values': {'excellent': 89900, 'good': 79900, 'fair': 69900, 'poor': 59900}
                },
                'pixel 8': {
                    'image_url': 'https://lh3.googleusercontent.com/HrUeaf_FE5-WjlFE9WOGdlYxFt7Z5MCSTp_cO9o7UH8cS4iL_PvKf8KlWe5rNNe8ZwF5mP_EhHrxbw=rw-e365-w1800',
                    'colors': ['Obsidian', 'Hazel', 'Rose'],
                    'storage_options': ['128GB', '256GB'],
                    'estimated_values': {'excellent': 69900, 'good': 59900, 'fair': 49900, 'poor': 39900}
                }
            }
        }
    
    def get_device_info(self, brand: str, model: str) -> Dict:
        """Get complete device information including stock image and estimated values"""
        try:
            brand_lower = brand.lower().strip()
            model_lower = model.lower().strip()
            
            if brand_lower in self.device_images:
                brand_data = self.device_images[brand_lower]
                
                # Try exact match first
                if model_lower in brand_data:
                    device_info = brand_data[model_lower].copy()
                    device_info['brand'] = brand
                    device_info['model'] = model
                    device_info['has_stock_image'] = True
                    return device_info
                
                # Try partial match
                for device_model, info in brand_data.items():
                    if model_lower in device_model or device_model in model_lower:
                        device_info = info.copy()
                        device_info['brand'] = brand
                        device_info['model'] = model
                        device_info['has_stock_image'] = True
                        return device_info
            
            # No stock image available
            return {
                'brand': brand,
                'model': model,
                'has_stock_image': False,
                'image_url': '/static/images/default-phone.svg',
                'colors': [],
                'storage_options': [],
                'estimated_values': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
            }
            
        except Exception as e:
            logger.error(f"Error getting device info for {brand} {model}: {e}")
            return {
                'brand': brand,
                'model': model,
                'has_stock_image': False,
                'image_url': '/static/images/default-phone.svg',
                'colors': [],
                'storage_options': [],
                'estimated_values': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
            }
    
    def get_stock_image_url(self, brand: str, model: str) -> str:
        """Get stock image URL for a device"""
        device_info = self.get_device_info(brand, model)
        return device_info.get('image_url', '/static/images/default-phone.svg')
    
    def get_estimated_value(self, brand: str, model: str, condition: str, storage: Optional[str] = None) -> int:
        """Get estimated value in cents for a device in specific condition"""
        device_info = self.get_device_info(brand, model)
        estimated_values = device_info.get('estimated_values', {})
        
        base_value = estimated_values.get(condition.lower(), 0)
        
        # Adjust value based on storage if specified
        if storage and base_value > 0:
            storage_upper = storage.upper()
            if '1TB' in storage_upper:
                base_value = int(base_value * 1.3)  # 30% more for 1TB
            elif '512GB' in storage_upper:
                base_value = int(base_value * 1.15)  # 15% more for 512GB
            elif '128GB' in storage_upper:
                base_value = int(base_value * 0.9)   # 10% less for base storage
        
        return base_value
    
    def search_devices(self, query: str) -> List[Dict]:
        """Search for devices matching a query"""
        results = []
        query_lower = query.lower()
        
        for brand, models in self.device_images.items():
            for model, info in models.items():
                full_name = f"{brand} {model}"
                if query_lower in full_name.lower():
                    result = {
                        'brand': brand.title(),
                        'model': model.title(),
                        'full_name': full_name.title(),
                        'image_url': info['image_url'],
                        'colors': info['colors'],
                        'storage_options': info['storage_options']
                    }
                    results.append(result)
        
        return results[:10]  # Limit to top 10 results

# Global instance
device_image_service = DeviceImageService()