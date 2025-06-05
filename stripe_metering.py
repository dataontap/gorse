
import stripe
import os
from datetime import datetime

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def report_data_usage(customer_id, megabytes_used, timestamp=None):
    """
    Report data usage to Stripe for metering and billing
    
    Args:
        customer_id (str): Stripe customer ID
        megabytes_used (float): Amount of data used in megabytes
        timestamp (datetime, optional): When the usage occurred. Defaults to now.
    
    Returns:
        dict: Result of the usage report
    """
    try:
        if not timestamp:
            timestamp = datetime.now()
        
        # Report usage event to Stripe
        event = stripe.billing.MeterEvent.create(
            event_name='data_usage',
            payload={
                'stripe_customer_id': customer_id,
                'megabytes_used': str(megabytes_used),
                'timestamp': timestamp.isoformat()
            },
            timestamp=int(timestamp.timestamp())
        )
        
        print(f"Reported {megabytes_used} MB usage for customer {customer_id}")
        return {
            'success': True,
            'event_id': event.identifier,
            'megabytes_used': megabytes_used,
            'customer_id': customer_id
        }
        
    except Exception as e:
        print(f"Error reporting data usage: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_customer_usage_summary(customer_id, start_date=None, end_date=None):
    """
    Get usage summary for a customer from Stripe
    
    Args:
        customer_id (str): Stripe customer ID
        start_date (datetime, optional): Start of period
        end_date (datetime, optional): End of period
    
    Returns:
        dict: Usage summary
    """
    try:
        # Get meter events for customer
        filters = {
            'customer': customer_id
        }
        
        if start_date:
            filters['created'] = {'gte': int(start_date.timestamp())}
        if end_date:
            filters['created'] = filters.get('created', {})
            filters['created']['lte'] = int(end_date.timestamp())
        
        # Note: In production, you'd use Stripe's usage records API
        # This is a simplified version for demonstration
        
        return {
            'success': True,
            'customer_id': customer_id,
            'total_usage_mb': 0,  # Would be calculated from actual events
            'billing_period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }
        
    except Exception as e:
        print(f"Error getting usage summary: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def create_usage_subscription(customer_id, price_id):
    """
    Create a usage-based subscription for a customer
    
    Args:
        customer_id (str): Stripe customer ID
        price_id (str): Price ID for usage-based billing
    
    Returns:
        dict: Subscription details
    """
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{
                'price': price_id,
            }],
            metadata={
                'type': 'usage_based',
                'service': 'data_consumption'
            }
        )
        
        print(f"Created usage subscription {subscription.id} for customer {customer_id}")
        return {
            'success': True,
            'subscription_id': subscription.id,
            'customer_id': customer_id,
            'status': subscription.status
        }
        
    except Exception as e:
        print(f"Error creating usage subscription: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Test the metering functions
    print("Testing Stripe metering functions...")
    
    # Example usage
    test_customer = "cus_test123"
    usage_result = report_data_usage(test_customer, 50.5)
    print(f"Usage report result: {usage_result}")
