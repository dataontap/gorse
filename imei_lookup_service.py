"""
IMEI Lookup Service - Detect device make/model from IMEI
"""
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class IMEILookupService:
    """Service for identifying devices from IMEI numbers"""
    
    def __init__(self):
        # TAC (Type Allocation Code) database - first 8 digits of IMEI
        # This is a simplified database for demo purposes
        self.tac_database = {
            # Apple iPhone models
            '35328609': {'brand': 'Apple', 'model': 'iPhone 15 Pro Max', 'device_type': 'smartphone'},
            '35328509': {'brand': 'Apple', 'model': 'iPhone 15 Pro', 'device_type': 'smartphone'},
            '35328409': {'brand': 'Apple', 'model': 'iPhone 15', 'device_type': 'smartphone'},
            '35716910': {'brand': 'Apple', 'model': 'iPhone 14 Pro Max', 'device_type': 'smartphone'},
            '35716810': {'brand': 'Apple', 'model': 'iPhone 14 Pro', 'device_type': 'smartphone'},
            '35716710': {'brand': 'Apple', 'model': 'iPhone 14', 'device_type': 'smartphone'},
            '35360810': {'brand': 'Apple', 'model': 'iPhone 13 Pro Max', 'device_type': 'smartphone'},
            '35360710': {'brand': 'Apple', 'model': 'iPhone 13 Pro', 'device_type': 'smartphone'},
            '35360610': {'brand': 'Apple', 'model': 'iPhone 13', 'device_type': 'smartphone'},
            
            # Samsung Galaxy models
            '35259510': {'brand': 'Samsung', 'model': 'Galaxy S24 Ultra', 'device_type': 'smartphone'},
            '35259410': {'brand': 'Samsung', 'model': 'Galaxy S24+', 'device_type': 'smartphone'},
            '35259310': {'brand': 'Samsung', 'model': 'Galaxy S24', 'device_type': 'smartphone'},
            '35227210': {'brand': 'Samsung', 'model': 'Galaxy S23 Ultra', 'device_type': 'smartphone'},
            '35227110': {'brand': 'Samsung', 'model': 'Galaxy S23+', 'device_type': 'smartphone'},
            '35227010': {'brand': 'Samsung', 'model': 'Galaxy S23', 'device_type': 'smartphone'},
            
            # Google Pixel models
            '35406810': {'brand': 'Google', 'model': 'Pixel 8 Pro', 'device_type': 'smartphone'},
            '35406710': {'brand': 'Google', 'model': 'Pixel 8', 'device_type': 'smartphone'},
            '35406610': {'brand': 'Google', 'model': 'Pixel 7 Pro', 'device_type': 'smartphone'},
            '35406510': {'brand': 'Google', 'model': 'Pixel 7', 'device_type': 'smartphone'},
        }
    
    def validate_imei(self, imei: str) -> bool:
        """Validate IMEI using Luhn algorithm"""
        try:
            # Remove any spaces or dashes
            imei = re.sub(r'[^0-9]', '', imei)
            
            # IMEI should be 15 digits
            if len(imei) != 15:
                return False
            
            # Luhn algorithm validation
            def luhn_checksum(card_num):
                def digits_of(number):
                    return [int(d) for d in str(number)]
                
                digits = digits_of(card_num)
                odd_digits = digits[-1::-2]
                even_digits = digits[-2::-2]
                checksum = sum(odd_digits)
                for digit in even_digits:
                    checksum += sum(digits_of(digit * 2))
                return checksum % 10
            
            return luhn_checksum(imei) == 0
            
        except Exception as e:
            logger.error(f"Error validating IMEI: {e}")
            return False
    
    def lookup_device_by_imei(self, imei: str) -> Dict:
        """Lookup device information by IMEI"""
        try:
            # Clean IMEI
            clean_imei = re.sub(r'[^0-9]', '', imei)
            
            if not self.validate_imei(clean_imei):
                return {
                    'success': False,
                    'error': 'Invalid IMEI format',
                    'imei_valid': False
                }
            
            # Extract TAC (first 8 digits)
            tac = clean_imei[:8]
            
            if tac in self.tac_database:
                device_info = self.tac_database[tac].copy()
                device_info['success'] = True
                device_info['imei'] = clean_imei
                device_info['imei_valid'] = True
                device_info['auto_detected'] = True
                device_info['confidence'] = 'high'
                return device_info
            else:
                # Try approximate matching for similar TACs
                for known_tac, info in self.tac_database.items():
                    if tac[:6] == known_tac[:6]:  # Match first 6 digits
                        device_info = info.copy()
                        device_info['success'] = True
                        device_info['imei'] = clean_imei
                        device_info['imei_valid'] = True
                        device_info['auto_detected'] = True
                        device_info['confidence'] = 'medium'
                        device_info['note'] = 'Similar device detected - please verify model'
                        return device_info
                
                return {
                    'success': False,
                    'error': 'Device not found in database',
                    'imei': clean_imei,
                    'imei_valid': True,
                    'suggested_action': 'Please select your device manually'
                }
                
        except Exception as e:
            logger.error(f"Error looking up IMEI {imei}: {e}")
            return {
                'success': False,
                'error': f'Lookup failed: {str(e)}',
                'imei_valid': False
            }
    
    def get_device_specs_from_imei(self, imei: str) -> Optional[Dict]:
        """Get additional device specifications if available"""
        try:
            device_info = self.lookup_device_by_imei(imei)
            
            if not device_info.get('success'):
                return None
            
            # Add additional specs based on known models
            brand = device_info.get('brand', '').lower()
            model = device_info.get('model', '').lower()
            
            specs = {
                'brand': device_info.get('brand'),
                'model': device_info.get('model'),
                'device_type': device_info.get('device_type', 'smartphone'),
                'auto_detected': True
            }
            
            # Add model-specific details
            if 'iphone' in model:
                specs.update({
                    'carrier_compatibility': ['Unlocked', 'Verizon', 'AT&T', 'T-Mobile'],
                    'network_type': '5G',
                    'typical_storage_options': ['128GB', '256GB', '512GB', '1TB']
                })
            elif 'galaxy' in model:
                specs.update({
                    'carrier_compatibility': ['Unlocked', 'Verizon', 'AT&T', 'T-Mobile'],
                    'network_type': '5G',
                    'typical_storage_options': ['128GB', '256GB', '512GB', '1TB']
                })
            elif 'pixel' in model:
                specs.update({
                    'carrier_compatibility': ['Unlocked', 'Verizon', 'AT&T', 'T-Mobile'],
                    'network_type': '5G',
                    'typical_storage_options': ['128GB', '256GB', '512GB']
                })
            
            return specs
            
        except Exception as e:
            logger.error(f"Error getting device specs for IMEI {imei}: {e}")
            return None

# Global instance
imei_lookup_service = IMEILookupService()