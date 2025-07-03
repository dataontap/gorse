
#!/usr/bin/env python3
"""
Create Stripe products for network features
Features ON by default: Priority >1Gbps Access, Video Optimization, US Home Route, Enhanced Security
Features OFF by default: Network Scans, voLTE (w/ HD Voice), Global Wi-Fi Calling, Global SAT TXT
"""

import os
import stripe
import psycopg2
from contextlib import contextmanager

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
database_url = os.environ.get('DATABASE_URL')

@contextmanager
def get_db_connection():
    connection = psycopg2.connect(database_url)
    try:
        yield connection
    finally:
        connection.close()

def create_network_features_table():
    """Create the network_features table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'network_features'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    cur.execute("""
                        CREATE TABLE network_features (
                            id SERIAL PRIMARY KEY,
                            stripe_product_id VARCHAR(100) UNIQUE NOT NULL,
                            feature_name VARCHAR(255) NOT NULL,
                            feature_title VARCHAR(255) NOT NULL,
                            description TEXT,
                            default_enabled BOOLEAN DEFAULT FALSE,
                            price_cents INTEGER DEFAULT 0,
                            eligibility_required BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    print("Created network_features table")
                else:
                    print("network_features table already exists")
    except Exception as e:
        print(f"Error creating network_features table: {str(e)}")

def create_stripe_network_products():
    """Create Stripe products for all network features"""
    
    # Network features configuration
    network_features = [
        {
            'stripe_id': 'network_scans',
            'name': 'Network Scans',
            'title': 'Network Scans',
            'description': 'Advanced network scanning and monitoring capabilities',
            'default_enabled': False,
            'price_cents': 0
        },
        {
            'stripe_id': 'priority_access',
            'name': 'Priority >1Gbps Access',
            'title': 'Priority access',
            'description': 'Provides prioritized network access during high congestion periods for more reliable connectivity.',
            'default_enabled': True,
            'price_cents': 0
        },
        {
            'stripe_id': 'video_optimization',
            'name': 'Video Optimization',
            'title': 'Video optimization',
            'description': 'Optimizes video streaming quality to reduce data usage while maintaining a good viewing experience.',
            'default_enabled': True,
            'price_cents': 0
        },
        {
            'stripe_id': 'us_home_route',
            'name': 'US Home Route',
            'title': 'VPN / Home route',
            'description': 'Creates a secure encrypted tunnel for your data and allows remote access to your home network.',
            'default_enabled': True,
            'price_cents': 0
        },
        {
            'stripe_id': 'enhanced_security',
            'name': 'Enhanced Security',
            'title': 'Private relay',
            'description': 'Routes your internet traffic through multiple relays to enhance privacy and hide your IP address.',
            'default_enabled': True,
            'price_cents': 0
        },
        {
            'stripe_id': 'volte_hd_voice',
            'name': 'voLTE (w/ HD Voice)',
            'title': 'voLTE (w/ HD Voice)',
            'description': 'High-definition voice calling over LTE network with enhanced call quality',
            'default_enabled': False,
            'price_cents': 0
        },
        {
            'stripe_id': 'global_wifi_calling',
            'name': 'Global Wi-Fi Calling',
            'title': 'Global Wi-Fi Calling',
            'description': 'Make and receive calls over Wi-Fi networks worldwide with seamless connectivity',
            'default_enabled': False,
            'price_cents': 0
        },
        {
            'stripe_id': 'global_sat_txt',
            'name': 'Global SAT TXT',
            'title': 'Global SAT TXT',
            'description': 'Send and receive text messages via satellite connection in remote areas without cellular coverage',
            'default_enabled': False,
            'price_cents': 0
        }
    ]
    
    print("Creating Stripe products for network features...")
    
    for feature in network_features:
        try:
            # Check if product already exists
            try:
                product = stripe.Product.retrieve(feature['stripe_id'])
                print(f"Product already exists: {feature['name']} ({product.id})")
            except stripe.error.InvalidRequestError:
                # Create the product if it doesn't exist
                product = stripe.Product.create(
                    id=feature['stripe_id'],
                    name=feature['name'],
                    description=feature['description'],
                    metadata={
                        'type': 'network_feature',
                        'product_catalog': 'network_services',
                        'default_enabled': str(feature['default_enabled']).lower(),
                        'feature_title': feature['title']
                    }
                )
                print(f"Created product: {feature['name']} ({product.id})")
            
            # Create free price for the feature (all features are currently free)
            try:
                prices = stripe.Price.list(product=feature['stripe_id'], active=True)
                if len(prices.data) == 0:
                    price = stripe.Price.create(
                        product=feature['stripe_id'],
                        unit_amount=feature['price_cents'],  # Free for now
                        currency='usd',
                        metadata={
                            'feature_type': 'network_service',
                            'default_enabled': str(feature['default_enabled']).lower()
                        }
                    )
                    print(f"Created price for {feature['name']}: ${feature['price_cents']/100:.2f}")
                else:
                    print(f"Price already exists for {feature['name']}: {prices.data[0].id}")
            except Exception as e:
                print(f"Error creating price for {feature['name']}: {str(e)}")
            
            # Store in database
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Check if feature already exists in database
                        cur.execute("""
                            SELECT id FROM network_features 
                            WHERE stripe_product_id = %s
                        """, (feature['stripe_id'],))
                        
                        existing = cur.fetchone()
                        
                        if not existing:
                            cur.execute("""
                                INSERT INTO network_features 
                                (stripe_product_id, feature_name, feature_title, description, 
                                 default_enabled, price_cents, eligibility_required)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                feature['stripe_id'],
                                feature['name'],
                                feature['title'],
                                feature['description'],
                                feature['default_enabled'],
                                feature['price_cents'],
                                False  # No eligibility required for now
                            ))
                            conn.commit()
                            print(f"Stored {feature['name']} in database")
                        else:
                            print(f"Feature {feature['name']} already exists in database")
            except Exception as e:
                print(f"Error storing {feature['name']} in database: {str(e)}")
                
        except Exception as e:
            print(f"Error creating product for {feature['name']}: {str(e)}")
    
    print("\nNetwork features setup completed!")
    print("\nFeatures ON by default:")
    for feature in network_features:
        if feature['default_enabled']:
            print(f"  ✓ {feature['name']}")
    
    print("\nFeatures OFF by default:")
    for feature in network_features:
        if not feature['default_enabled']:
            print(f"  ○ {feature['name']}")

def get_network_features():
    """Get all network features from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT stripe_product_id, feature_name, feature_title, description,
                           default_enabled, price_cents, eligibility_required
                    FROM network_features
                    ORDER BY feature_name
                """)
                
                features = []
                for row in cur.fetchall():
                    features.append({
                        'stripe_product_id': row[0],
                        'feature_name': row[1],
                        'feature_title': row[2],
                        'description': row[3],
                        'default_enabled': row[4],
                        'price_cents': row[5],
                        'eligibility_required': row[6]
                    })
                
                return features
    except Exception as e:
        print(f"Error retrieving network features: {str(e)}")
        return []

def update_feature_pricing(stripe_product_id, new_price_cents):
    """Update pricing for a network feature"""
    try:
        # Create new price in Stripe
        new_price = stripe.Price.create(
            product=stripe_product_id,
            unit_amount=new_price_cents,
            currency='usd',
            metadata={
                'feature_type': 'network_service',
                'updated_pricing': 'true'
            }
        )
        
        # Update database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE network_features 
                    SET price_cents = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE stripe_product_id = %s
                """, (new_price_cents, stripe_product_id))
                conn.commit()
        
        print(f"Updated pricing for {stripe_product_id}: ${new_price_cents/100:.2f}")
        return new_price.id
        
    except Exception as e:
        print(f"Error updating pricing for {stripe_product_id}: {str(e)}")
        return None

if __name__ == "__main__":
    print("Setting up network features in Stripe and database...")
    
    # Create database table
    create_network_features_table()
    
    # Create Stripe products and store in database
    create_stripe_network_products()
    
    # Display current features
    print("\nCurrent network features:")
    features = get_network_features()
    for feature in features:
        status = "ON" if feature['default_enabled'] else "OFF"
        price = f"${feature['price_cents']/100:.2f}" if feature['price_cents'] > 0 else "FREE"
        print(f"  {status:3} | {price:6} | {feature['feature_name']}")
