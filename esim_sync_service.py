"""
eSIM Data Synchronization Service
Handles reconciliation between OXIO API and local database
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


def reconcile_oxio_line_to_database(firebase_uid: str, user_id: int, line_data: Dict[str, Any], conn) -> Dict[str, Any]:
    """
    Reconcile a single OXIO line into local database tables
    
    Args:
        firebase_uid: Firebase user ID
        user_id: Internal database user ID
        line_data: OXIO line data from API
        conn: Database connection
        
    Returns:
        Dictionary with reconciliation results
    """
    try:
        cursor = conn.cursor()
        results = {
            'iccid_updated': False,
            'activation_updated': False,
            'purchase_created': False,
            'errors': []
        }
        
        # Extract line details
        line_id = line_data.get('lineId', '')
        status = line_data.get('status', 'UNKNOWN')
        
        # Extract SIM details
        sim_info = line_data.get('sim', {})
        iccid = sim_info.get('iccid', '')
        activation_code = sim_info.get('activationCode', '')
        activation_url = sim_info.get('activationUrl', '')
        country = sim_info.get('countryCode', 'US')
        
        # Extract phone number
        phone_numbers = line_data.get('phoneNumbers', [])
        phone_number = phone_numbers[0].get('phoneNumber', '') if phone_numbers else ''
        
        if not iccid or not line_id:
            results['errors'].append('Missing required ICCID or Line ID from OXIO data')
            return results
        
        print(f"📊 Reconciling OXIO line: ICCID={iccid}, Line ID={line_id}, Status={status}")
        
        # Step 1: Upsert into iccid_inventory
        try:
            cursor.execute("""
                INSERT INTO iccid_inventory 
                    (iccid, lpa_code, country, status, allocated_to_firebase_uid, assigned_at, line_id)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT (iccid) 
                DO UPDATE SET
                    lpa_code = EXCLUDED.lpa_code,
                    status = 'assigned',
                    allocated_to_firebase_uid = EXCLUDED.allocated_to_firebase_uid,
                    assigned_at = NOW(),
                    line_id = EXCLUDED.line_id
            """, (iccid, activation_code or activation_url, country, 'assigned', firebase_uid, line_id))
            
            results['iccid_updated'] = True
            print(f"✅ ICCID inventory updated for {iccid}")
        except Exception as iccid_error:
            results['errors'].append(f'ICCID update failed: {str(iccid_error)}')
            print(f"❌ ICCID update failed: {iccid_error}")
        
        # Step 2: Upsert into oxio_activations
        try:
            # Map OXIO status to our activation status
            activation_status = 'activated' if status in ['ACTIVE', 'INITIATING'] else 'pending'
            
            # Store full OXIO response for debugging
            oxio_response_json = json.dumps({
                'success': True,
                'data': line_data,
                'synced_from_oxio': True,
                'sync_timestamp': datetime.now().isoformat()
            })
            
            cursor.execute("""
                INSERT INTO oxio_activations 
                    (user_id, firebase_uid, product_id, iccid, line_id, phone_number, 
                     activation_status, esim_qr_code, activation_url, activation_code, 
                     oxio_response, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id, iccid) 
                DO UPDATE SET
                    line_id = EXCLUDED.line_id,
                    phone_number = EXCLUDED.phone_number,
                    activation_status = EXCLUDED.activation_status,
                    activation_url = EXCLUDED.activation_url,
                    activation_code = EXCLUDED.activation_code,
                    oxio_response = EXCLUDED.oxio_response
            """, (
                user_id, firebase_uid, 'esim_beta', iccid, line_id, phone_number,
                activation_status, None, activation_url, activation_code, oxio_response_json
            ))
            
            results['activation_updated'] = True
            print(f"✅ OXIO activation updated for {iccid}")
        except Exception as activation_error:
            results['errors'].append(f'Activation update failed: {str(activation_error)}')
            print(f"❌ Activation update failed: {activation_error}")
        
        # Step 3: Ensure purchase record exists (create minimal record if missing)
        try:
            # Check if purchase already exists
            cursor.execute("""
                SELECT purchaseid FROM purchases 
                WHERE firebaseuid = %s AND stripeproductid = 'esim_beta'
                LIMIT 1
            """, (firebase_uid,))
            
            existing_purchase = cursor.fetchone()
            
            if not existing_purchase:
                # Create minimal purchase record tagged as recovered from OXIO
                cursor.execute("""
                    INSERT INTO purchases 
                        (stripeid, stripeproductid, priceid, totalamount, datecreated, 
                         userid, stripetransactionid, firebaseuid)
                    VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)
                """, (
                    f'recovered_from_oxio_{firebase_uid}_{int(datetime.now().timestamp())}',
                    'esim_beta',
                    'price_1S7Yc6JnTfh0bNQQVeLeprXe',
                    100,  # $1.00 in cents
                    user_id,
                    'recovered_from_oxio',
                    firebase_uid
                ))
                
                results['purchase_created'] = True
                print(f"✅ Purchase record created (recovered from OXIO)")
            else:
                print(f"ℹ️  Purchase record already exists")
        except Exception as purchase_error:
            results['errors'].append(f'Purchase creation failed: {str(purchase_error)}')
            print(f"❌ Purchase creation failed: {purchase_error}")
        
        # Commit changes
        conn.commit()
        
        return results
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Reconciliation failed: {str(e)}")
        return {
            'iccid_updated': False,
            'activation_updated': False,
            'purchase_created': False,
            'errors': [f'Reconciliation error: {str(e)}']
        }


def sync_oxio_lines_for_user(firebase_uid: str, oxio_user_id: str, conn) -> Dict[str, Any]:
    """
    Fetch lines from OXIO and reconcile them into local database
    
    Args:
        firebase_uid: Firebase user ID
        oxio_user_id: OXIO user ID
        conn: Database connection
        
    Returns:
        Dictionary with sync results
    """
    try:
        from oxio_service import OXIOService
        
        cursor = conn.cursor()
        
        # Get user_id from users table
        cursor.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return {
                'success': False,
                'error': 'User not found in database',
                'lines_synced': 0
            }
        
        user_id = user_row[0]
        
        # Fetch lines from OXIO
        oxio_service = OXIOService()
        lines_response = oxio_service.get_user_lines(oxio_user_id)
        
        if not lines_response.get('success'):
            return {
                'success': False,
                'error': lines_response.get('error', 'Failed to fetch lines from OXIO'),
                'message': lines_response.get('message', ''),
                'lines_synced': 0
            }
        
        # Extract lines from response
        lines_data = lines_response.get('data', {})
        lines_list = lines_data.get('lines', [])
        
        if not lines_list:
            return {
                'success': True,
                'message': 'No lines found in OXIO for this user',
                'lines_synced': 0,
                'user_should_purchase': True
            }
        
        # Reconcile each line
        sync_results = []
        for line in lines_list:
            result = reconcile_oxio_line_to_database(firebase_uid, user_id, line, conn)
            sync_results.append(result)
        
        # Summary
        total_synced = sum(1 for r in sync_results if r['activation_updated'])
        total_errors = sum(len(r['errors']) for r in sync_results)
        
        return {
            'success': True,
            'lines_synced': total_synced,
            'total_lines': len(lines_list),
            'errors_count': total_errors,
            'sync_details': sync_results,
            'message': f'Synced {total_synced} of {len(lines_list)} lines from OXIO'
        }
        
    except Exception as e:
        print(f"❌ OXIO sync failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'lines_synced': 0
        }
