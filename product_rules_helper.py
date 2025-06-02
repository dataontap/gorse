
import os
from typing import Optional, Dict, Any
from main import get_db_connection

def get_product_rules(stripe_product_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve product rules from database by Stripe product ID"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT rule_id, stripe_product_id, product_name, one_time_charge,
                               weekly_charge, monthly_charge, yearly_charge, 
                               token_reward_percentage, additional_rules
                        FROM product_rules 
                        WHERE stripe_product_id = %s
                    """, (stripe_product_id,))
                    
                    result = cur.fetchone()
                    if result:
                        return {
                            'rule_id': result[0],
                            'stripe_product_id': result[1],
                            'product_name': result[2],
                            'one_time_charge': float(result[3]) if result[3] else 0.0,
                            'weekly_charge': float(result[4]) if result[4] else 0.0,
                            'monthly_charge': float(result[5]) if result[5] else 0.0,
                            'yearly_charge': float(result[6]) if result[6] else 0.0,
                            'token_reward_percentage': float(result[7]) if result[7] else 1.0,
                            'additional_rules': result[8]
                        }
        return None
    except Exception as e:
        print(f"Error retrieving product rules: {str(e)}")
        return None

def update_product_rules(stripe_product_id: str, **kwargs) -> bool:
    """Update product rules for a given Stripe product ID"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Build dynamic update query
                    updates = []
                    values = []
                    
                    for key, value in kwargs.items():
                        if key in ['product_name', 'one_time_charge', 'weekly_charge', 
                                  'monthly_charge', 'yearly_charge', 'token_reward_percentage', 
                                  'additional_rules']:
                            updates.append(f"{key} = %s")
                            values.append(value)
                    
                    if updates:
                        updates.append("updated_at = CURRENT_TIMESTAMP")
                        values.append(stripe_product_id)
                        
                        query = f"""
                            UPDATE product_rules 
                            SET {', '.join(updates)}
                            WHERE stripe_product_id = %s
                        """
                        
                        cur.execute(query, values)
                        conn.commit()
                        return cur.rowcount > 0
        return False
    except Exception as e:
        print(f"Error updating product rules: {str(e)}")
        return False

def get_all_product_rules() -> list:
    """Get all product rules from database"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT rule_id, stripe_product_id, product_name, one_time_charge,
                               weekly_charge, monthly_charge, yearly_charge, 
                               token_reward_percentage, additional_rules, created_at
                        FROM product_rules 
                        ORDER BY created_at DESC
                    """)
                    
                    results = cur.fetchall()
                    return [{
                        'rule_id': row[0],
                        'stripe_product_id': row[1],
                        'product_name': row[2],
                        'one_time_charge': float(row[3]) if row[3] else 0.0,
                        'weekly_charge': float(row[4]) if row[4] else 0.0,
                        'monthly_charge': float(row[5]) if row[5] else 0.0,
                        'yearly_charge': float(row[6]) if row[6] else 0.0,
                        'token_reward_percentage': float(row[7]) if row[7] else 1.0,
                        'additional_rules': row[8],
                        'created_at': row[9].isoformat() if row[9] else None
                    } for row in results]
        return []
    except Exception as e:
        print(f"Error retrieving all product rules: {str(e)}")
        return []
