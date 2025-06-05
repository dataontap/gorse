
import os
import stripe
import time

# Initialize Stripe with your API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def create_stripe_products():
    """Creates all necessary products and prices in Stripe"""
    
    print("Setting up Stripe products...")
    
    # 1. Global Data - One-time purchase
    try:
        # Check if product already exists
        try:
            global_data_product = stripe.Product.retrieve('global_data_10gb')
            print(f"Global Data product already exists: {global_data_product.id}")
        except stripe.error.InvalidRequestError:
            # Create the product if it doesn't exist
            global_data_product = stripe.Product.create(
                id='global_data_10gb',
                name='Global Data 10GB',
                description='10GB of shareable data for global use',
                metadata={
                    'type': 'data',
                    'product_catalog': 'digital_services',
                    'data_amount': '10'
                }
            )
            print(f"Created Global Data product: {global_data_product.id}")
        
        # Create price for Global Data
        try:
            prices = stripe.Price.list(product=global_data_product.id, active=True)
            if len(prices.data) == 0:
                global_data_price = stripe.Price.create(
                    product=global_data_product.id,
                    unit_amount=1000,  # $10.00
                    currency='usd',
                    metadata={
                        'data_amount': '10GB'
                    }
                )
                print(f"Created Global Data price: {global_data_price.id}")
            else:
                print(f"Global Data price already exists: {prices.data[0].id}")
        except Exception as e:
            print(f"Error creating Global Data price: {str(e)}")
            
        # 2. Basic Membership - Subscription
        try:
            basic_membership_product = stripe.Product.retrieve('basic_membership')
            print(f"Basic Membership product already exists: {basic_membership_product.id}")
        except stripe.error.InvalidRequestError:
            basic_membership_product = stripe.Product.create(
                id='basic_membership',
                name='Basic Membership',
                description='Global data access, 2FA & Satellite eTXT, $24/year',
                metadata={
                    'type': 'subscription',
                    'product_catalog': 'memberships',
                    'tier': 'basic'
                }
            )
            print(f"Created Basic Membership product: {basic_membership_product.id}")
        
        # Create price for Basic Membership
        try:
            prices = stripe.Price.list(product=basic_membership_product.id, active=True)
            if len(prices.data) == 0:
                basic_membership_price = stripe.Price.create(
                    product=basic_membership_product.id,
                    unit_amount=2400,  # $24.00
                    currency='usd',
                    recurring={
                        'interval': 'year'
                    },
                    metadata={
                        'tier': 'basic'
                    }
                )
                print(f"Created Basic Membership price: {basic_membership_price.id}")
            else:
                print(f"Basic Membership price already exists: {prices.data[0].id}")
        except Exception as e:
            print(f"Error creating Basic Membership price: {str(e)}")
        
        # 3. Full Membership - Subscription
        try:
            full_membership_product = stripe.Product.retrieve('full_membership')
            print(f"Full Membership product already exists: {full_membership_product.id}")
        except stripe.error.InvalidRequestError:
            full_membership_product = stripe.Product.create(
                id='full_membership',
                name='Full Membership',
                description='Unlimited Talk + Text, Global Wi-Fi Calling & Satellite eTXT, $66/year',
                metadata={
                    'type': 'subscription',
                    'product_catalog': 'memberships',
                    'tier': 'full'
                }
            )
            print(f"Created Full Membership product: {full_membership_product.id}")
        
        # Create price for Full Membership
        try:
            prices = stripe.Price.list(product=full_membership_product.id, active=True)
            if len(prices.data) == 0:
                full_membership_price = stripe.Price.create(
                    product=full_membership_product.id,
                    unit_amount=6600,  # $66.00
                    currency='usd',
                    recurring={
                        'interval': 'year'
                    },
                    metadata={
                        'tier': 'full'
                    }
                )
                print(f"Created Full Membership price: {full_membership_price.id}")
            else:
                print(f"Full Membership price already exists: {prices.data[0].id}")
        except Exception as e:
            print(f"Error creating Full Membership price: {str(e)}")
            
        # 4. Metal DOTM Card - One-time purchase
        try:
            metal_card_product = stripe.Product.retrieve('metal_card')
            print(f"Metal Card product already exists: {metal_card_product.id}")
        except stripe.error.InvalidRequestError:
            metal_card_product = stripe.Product.create(
                id='metal_card',
                name='DOTM Metal Card',
                description='Premium metal cryptocurrency card powered by MetaMask',
                metadata={
                    'type': 'physical',
                    'product_catalog': 'cards',
                    'material': 'metal'
                }
            )
            print(f"Created Metal Card product: {metal_card_product.id}")
        
        # Create price for Metal Card
        try:
            prices = stripe.Price.list(product=metal_card_product.id, active=True)
            if len(prices.data) == 0:
                metal_card_price = stripe.Price.create(
                    product=metal_card_product.id,
                    unit_amount=9999,  # $99.99
                    currency='usd',
                    metadata={
                        'card_type': 'metal'
                    }
                )
                print(f"Created Metal Card price: {metal_card_price.id}")
            else:
                print(f"Metal Card price already exists: {prices.data[0].id}")
        except Exception as e:
            print(f"Error creating Metal Card price: {str(e)}")
        
        # 5. Create Meter for Data Usage Tracking
        try:
            # Check if meter already exists
            meters = stripe.billing.Meter.list(limit=100)
            data_meter = None
            for meter in meters.data:
                if meter.event_name == 'data_usage':
                    data_meter = meter
                    print(f"Data usage meter already exists: {meter.id}")
                    break
            
            if not data_meter:
                data_meter = stripe.billing.Meter.create(
                    display_name='Data Usage',
                    event_name='data_usage',
                    value_settings={
                        'event_payload_key': 'megabytes_used'
                    }
                )
                print(f"Created data usage meter: {data_meter.id}")
                
            # Create usage-based pricing for existing products
            try:
                # Add usage-based price to global data product
                usage_prices = stripe.Price.list(product='global_data_10gb', type='recurring')
                if len(usage_prices.data) == 0:
                    usage_price = stripe.Price.create(
                        product='global_data_10gb',
                        currency='usd',
                        recurring={
                            'interval': 'month',
                            'usage_type': 'metered',
                            'meter': data_meter.id
                        },
                        billing_scheme='per_unit',
                        unit_amount=10,  # $0.10 per MB
                        metadata={
                            'usage_type': 'data_consumption'
                        }
                    )
                    print(f"Created usage-based price: {usage_price.id}")
                else:
                    print(f"Usage-based price already exists: {usage_prices.data[0].id}")
            except Exception as e:
                print(f"Error creating usage-based price: {str(e)}")
                
        except Exception as e:
            print(f"Error setting up data usage meter: {str(e)}")

        print("Stripe products setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up Stripe products: {str(e)}")
        return False

if __name__ == "__main__":
    create_stripe_products()
