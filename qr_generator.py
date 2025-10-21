#!/usr/bin/env python3
"""
QR Code Generator for RESIN Information
Generates QR codes for phone numbers and RESIN data
"""

import qrcode
import qrcode.image.svg
import base64
import json
from io import BytesIO
from typing import Dict, Any

def generate_resin_qr_code(phone_number: str, group_id: str, oxio_user_id: str, 
                          additional_data: Dict = None) -> str:
    """
    Generate QR code for RESIN information

    Args:
        phone_number: The assigned phone number
        group_id: OXIO Group ID
        oxio_user_id: OXIO User ID
        additional_data: Additional RESIN data (optional)

    Returns:
        Base64 encoded PNG image of the QR code
    """
    try:
        # Create RESIN data structure
        resin_data = {
            'type': 'DOTM_RESIN',
            'phone_number': phone_number,
            'group_id': group_id,
            'oxio_user_id': oxio_user_id,
            'version': '1.0',
            'generated_at': json.dumps({'$date': {'$numberLong': str(int(__import__('time').time() * 1000))}}),
            'platform': 'DOTM'
        }

        # Add additional data if provided
        if additional_data:
            resin_data.update(additional_data)

        # Convert to JSON string
        qr_data = json.dumps(resin_data, separators=(',', ':'))

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Always return with data URI prefix
        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return None

def generate_simple_phone_qr(phone_number: str) -> str:
    """
    Generate simple QR code for phone number

    Args:
        phone_number: Phone number to encode

    Returns:
        Base64 encoded PNG image of the QR code
    """
    try:
        # Generate QR code for phone number
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=4,
        )
        qr.add_data(f"tel:{phone_number}")
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Always return with data URI prefix
        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"Error generating simple QR code: {str(e)}")
        return None

def generate_activation_qr(activation_data: Dict[str, Any]) -> str:
    """
    Generate QR code for eSIM activation data

    Args:
        activation_data: Dictionary containing activation information

    Returns:
        Base64 encoded PNG image of the QR code
    """
    try:
        # Generate QR code for activation data
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )

        qr_data = json.dumps(activation_data, separators=(',', ':'))
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Always return with data URI prefix
        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"Error generating activation QR code: {str(e)}")
        return None

def generate_qr_code_for_lpa(lpa_code: str) -> Dict[str, Any]:
    """
    Generate QR code for LPA (Local Profile Assistant) code used in eSIM activation

    Args:
        lpa_code: LPA code string (e.g., LPA:1$consumer.e-sim.global$OX202409053801001503346)

    Returns:
        Dictionary with success status, filename, file_size_bytes, and lpa_code
    """
    try:
        import os
        import tempfile

        # Generate QR code for LPA code
        qr = qrcode.QRCode(
            version=2,  # Handles longer LPA codes
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(lpa_code)
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to temporary file for email attachments
        temp_dir = tempfile.gettempdir()
        filename = os.path.join(temp_dir, f"esim_qr_{int(__import__('time').time())}.png")
        img.save(filename, format="PNG")

        # Get file size
        file_size = os.path.getsize(filename)

        return {
            'success': True,
            'filename': filename,
            'file_size_bytes': file_size,
            'lpa_code': lpa_code,
            'message': 'QR code generated successfully'
        }

    except Exception as e:
        print(f"Error generating LPA QR code: {str(e)}")
        return {
            'success': False,
            'filename': None,
            'file_size_bytes': 0,
            'lpa_code': lpa_code,
            'message': f'Error: {str(e)}'
        }