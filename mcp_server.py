
#!/usr/bin/env python3
"""
MCP Server for DOTM Platform Services
Provides detailed information about available services, pricing, and options
Accessible at get-dot-eSIM.replit.app/mcp
"""

from flask import Flask, jsonify, render_template_string
import os
from datetime import datetime

# Remove Flask app instance - routes will be handled by main.py

# Service catalog with detailed pricing and options
SERVICES_CATALOG = {
    "esim_services": {
        "title": "Connectivity Services",
        "description": "Global eSIM connectivity and activation services",
        "services": [
            {
                "id": "global_data_10gb",
                "name": "Global Data 10GB",
                "description": "10GB of shareable data for global use",
                "type": "one_time_purchase",
                "price_usd": 10.00,
                "features": [
                    "10GB data allowance",
                    "Global coverage",
                    "Shareable data",
                    "No expiration"
                ],
                "availability": "Available"
            },
            {
                "id": "beta_esim_activation",
                "name": "Beta eSIM Activation",
                "description": "Beta testing program with 10-day demo plan",
                "type": "beta_program",
                "price_usd": 1.00,
                "features": [
                    "1000MB data allowance",
                    "10-day validity",
                    "Global coverage",
                    "Beta program access"
                ],
                "availability": "Beta Testing"
            }
        ]
    },
    "membership_plans": {
        "title": "Membership Plans",
        "description": "Annual subscription plans with exclusive benefits",
        "services": [
            {
                "id": "basic_membership",
                "name": "Basic Membership",
                "description": "GLOBAL DATA ACCESS + 2FA SMS",
                "type": "annual_subscription",
                "price_cad": 24.0,
                "billing_cycle": "yearly",
                "features": [
                    "Global data access",
                    "$1 per GB of data bonus - limited availability",
                    "2FA support via incoming SMS only",
                    "eSIM line activation included",
                    "Unlimited Hotspot",
                    "Infinite data share with any member",
                    "Curated marketplace",
                    "Network quality and outage detection",
                    "Connectivity and device insights",
                    "Device insurance and protection",
                    "Device auctions",
                    "Other retail services",
                    "Priority QCI-8 and 5G+ access where available",
                    "Premium live person callback support",
                    "1.33 DOTM for $10 purchase",
                    "All prices are in CAD"
                ],
                "availability": "Available"
            },
            {
                "id": "full_membership",
                "name": "Full Membership",
                "description": "Unlimited Talk + Text, Global Wi-Fi Calling & Satellite eTXT",
                "type": "annual_subscription",
                "price_usd": 66.0,
                "billing_cycle": "yearly (365.25 days)",
                "features": [
                    "Unlimited talk and text in North America - Canada, US, Mexico",
                    "Wi-Fi Calling access globally",
                    "Satellite D2C (Available in 2026)"
                ],
                "availability": "Available"
            },
            {
                "id": "beta_tester",
                "name": "Beta Tester Program",
                "description": "Free access to beta features and early releases",
                "type": "monthly_subscription",
                "price_usd": 0.00,
                "billing_cycle": "monthly",
                "features": [
                    "Free beta access",
                    "Early feature releases",
                    "Community feedback program",
                    "Testing privileges"
                ],
                "availability": "Invitation Only"
            }
        ]
    },
    "physical_products": {
        "title": "Physical Products",
        "description": "Hardware and physical items",
        "services": [
            {
                "id": "metal_card",
                "name": "DOTM Metal Card",
                "description": "Premium metal cryptocurrency card powered by MetaMask",
                "type": "one_time_purchase",
                "price_usd": 99.99,
                "features": [
                    "Premium metal construction",
                    "MetaMask integration",
                    "Cryptocurrency support",
                    "Collector's item",
                    "Global shipping included"
                ],
                "availability": "Limited Edition"
            }
        ]
    },
    "network_features": {
        "title": "Network Features",
        "description": "Advanced network capabilities and optimizations",
        "services": [
            {
                "id": "network_scans",
                "name": "Network Scans",
                "description": "Advanced network scanning and monitoring capabilities",
                "type": "add_on",
                "price_usd": 0.00,
                "billing_cycle": "monthly",
                "features": [
                    "Network discovery",
                    "Port scanning",
                    "Security assessment",
                    "Real-time monitoring"
                ],
                "availability": "Free"
            },
            {
                "id": "network_security_basic",
                "name": "Network Security",
                "description": "Basic network security features including firewall and threat detection",
                "type": "add_on",
                "price_usd": 5.00,
                "billing_cycle": "monthly",
                "features": [
                    "Firewall protection",
                    "Threat detection",
                    "Security monitoring",
                    "Basic DDoS protection"
                ],
                "availability": "Available",
                "default_enabled": True
            },
            {
                "id": "network_optimization",
                "name": "Network Optimization",
                "description": "Optimize network performance and reduce latency",
                "type": "add_on",
                "price_usd": 3.00,
                "billing_cycle": "monthly",
                "features": [
                    "Latency optimization",
                    "Bandwidth management",
                    "Connection prioritization",
                    "Performance analytics"
                ],
                "availability": "Available"
            },
            {
                "id": "network_monitoring",
                "name": "Network Monitoring",
                "description": "Real-time network monitoring and analytics dashboard",
                "type": "add_on",
                "price_usd": 4.00,
                "billing_cycle": "monthly",
                "features": [
                    "Real-time monitoring",
                    "Analytics dashboard",
                    "Performance metrics",
                    "Historical data"
                ],
                "availability": "Available"
            },
            {
                "id": "network_vpn_access",
                "name": "VPN Access",
                "description": "Secure VPN access with global server locations",
                "type": "add_on",
                "price_usd": 8.00,
                "billing_cycle": "monthly",
                "features": [
                    "Global server network",
                    "Military-grade encryption",
                    "No-logs policy",
                    "Multiple protocols"
                ],
                "availability": "Available"
            },
            {
                "id": "network_priority_routing",
                "name": "Priority Routing",
                "description": "Priority network routing for improved connection speeds",
                "type": "add_on",
                "price_usd": 6.00,
                "billing_cycle": "monthly",
                "features": [
                    "Priority traffic routing",
                    "Reduced latency",
                    "Improved speeds",
                    "Traffic optimization"
                ],
                "availability": "Available"
            }
        ]
    },
    "token_services": {
        "title": "DOTM Token Services",
        "description": "Cryptocurrency token services and rewards",
        "services": [
            {
                "id": "founding_member_token",
                "name": "Founding Member Token",
                "description": "100 DOTM tokens for founding members",
                "type": "one_time_reward",
                "price_usd": 0.00,
                "token_amount": "100 DOTM",
                "features": [
                    "Founding member status",
                    "100 DOTM tokens",
                    "Special privileges",
                    "Community recognition"
                ],
                "availability": "Founding Members Only"
            },
            {
                "id": "new_member_token",
                "name": "New Member Welcome Token",
                "description": "1 DOTM token for new registrations",
                "type": "welcome_reward",
                "price_usd": 0.00,
                "token_amount": "1 DOTM",
                "features": [
                    "Welcome bonus",
                    "Automatic upon registration",
                    "Sepolia testnet wallet included"
                ],
                "availability": "All New Members"
            },
            {
                "id": "purchase_rewards",
                "name": "Purchase Rewards",
                "description": "10.33% token rewards on marketplace purchases",
                "type": "cashback_reward",
                "price_usd": 0.00,
                "reward_percentage": "10.33%",
                "features": [
                    "10.33% of purchase amount in DOTM",
                    "Automatic distribution",
                    "All marketplace purchases eligible"
                ],
                "availability": "All Purchases"
            }
        ]
    },
    "api_services": {
        "title": "API Services",
        "description": "Developer and integration services",
        "services": [
            {
                "id": "oxio_integration",
                "name": "OXIO Line Activation",
                "description": "Automatic mobile line activation via OXIO API",
                "type": "included_service",
                "price_usd": 0.00,
                "features": [
                    "Automatic with Basic Membership",
                    "Global mobile connectivity",
                    "eSIM profile generation",
                    "Real-time activation"
                ],
                "availability": "Membership Required"
            },
            {
                "id": "stripe_integration",
                "name": "Payment Processing",
                "description": "Secure payment processing via Stripe",
                "type": "payment_processing",
                "price_usd": 0.00,
                "processing_fee": "2.9% + $0.30 per transaction",
                "features": [
                    "Credit card processing",
                    "Subscription management",
                    "International payments",
                    "Secure checkout"
                ],
                "availability": "All Services"
            }
        ]
    },
    "support_services": {
        "title": "Support Services",
        "description": "Customer support and assistance",
        "services": [
            {
                "id": "standard_support",
                "name": "Standard Support",
                "description": "Basic customer support via help desk",
                "type": "included_service",
                "price_usd": 0.00,
                "response_time": "24-48 hours",
                "features": [
                    "Email support",
                    "Help desk system",
                    "FAQ resources",
                    "Community forums"
                ],
                "availability": "All Users"
            },
            {
                "id": "priority_support",
                "name": "Priority Support",
                "description": "Priority customer support for members",
                "type": "membership_benefit",
                "price_usd": 0.00,
                "response_time": "4-8 hours",
                "features": [
                    "Priority queue",
                    "Direct access",
                    "Phone support",
                    "Technical assistance"
                ],
                "availability": "Basic/Full Members"
            },
            {
                "id": "premium_support",
                "name": "Premium Support",
                "description": "Premium support with dedicated assistance",
                "type": "membership_benefit",
                "price_usd": 0.00,
                "response_time": "1-2 hours",
                "features": [
                    "Dedicated support agent",
                    "24/7 availability",
                    "Video support",
                    "Custom solutions"
                ],
                "availability": "Full Members Only"
            }
        ]
    }
}

def calculate_total_costs():
    """Calculate potential monthly and yearly costs"""
    costs = {
        "minimum_monthly": 0.00,
        "basic_monthly": 2.00,  # Basic membership / 12
        "full_monthly": 5.50,   # Full membership / 12
        "maximum_monthly": 0.00
    }
    
    # Calculate maximum monthly with all add-ons
    network_addons = SERVICES_CATALOG["network_features"]["services"]
    max_addon_cost = sum(service["price_usd"] for service in network_addons if service["price_usd"] > 0)
    
    costs["maximum_monthly"] = costs["full_monthly"] + max_addon_cost
    
    # Yearly equivalents
    costs["basic_yearly"] = 24.00
    costs["full_yearly"] = 66.00
    costs["maximum_yearly"] = costs["maximum_monthly"] * 12
    
    return costs

def mcp_server():
    """Main MCP server endpoint"""
    costs = calculate_total_costs()
    
    mcp_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOTM Platform - Service Catalog & Pricing</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 30px;
        }
        .cost-summary {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 4px solid #3498db;
        }
        .cost-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .cost-item {
            background: white;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
        .cost-item h4 {
            margin: 0 0 5px;
            color: #2c3e50;
        }
        .cost-item .price {
            font-size: 1.3em;
            font-weight: bold;
            color: #27ae60;
        }
        .service-category {
            margin-bottom: 40px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }
        .category-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        .category-header h2 {
            margin: 0 0 5px;
            color: #2c3e50;
        }
        .category-header p {
            margin: 0;
            color: #6c757d;
        }
        .services-grid {
            display: grid;
            gap: 0;
        }
        .service-item {
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            background: white;
        }
        .service-item:last-child {
            border-bottom: none;
        }
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }
        .service-info h3 {
            margin: 0 0 5px;
            color: #2c3e50;
        }
        .service-info p {
            margin: 0;
            color: #6c757d;
            font-size: 0.9em;
        }
        .service-pricing {
            text-align: right;
        }
        .price-main {
            font-size: 1.5em;
            font-weight: bold;
            color: #27ae60;
        }
        .price-cycle {
            font-size: 0.8em;
            color: #6c757d;
        }
        .availability {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 5px;
        }
        .available { background: #d4edda; color: #155724; }
        .beta { background: #fff3cd; color: #856404; }
        .invitation { background: #d1ecf1; color: #0c5460; }
        .limited { background: #f8d7da; color: #721c24; }
        .members { background: #e2e3e5; color: #383d41; }
        .features {
            margin: 10px 0;
        }
        .features ul {
            margin: 5px 0;
            padding-left: 18px;
        }
        .features li {
            margin: 3px 0;
            font-size: 0.9em;
        }
        .mcp-info {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }
        .mcp-info h3 {
            margin: 0 0 10px;
            color: #1976d2;
        }
        .api-endpoint {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            margin: 10px 0;
        }
        @media (max-width: 768px) {
            .service-header {
                flex-direction: column;
            }
            .service-pricing {
                text-align: left;
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DOTM Platform</h1>
            <p>Complete Service Catalog & Pricing Guide</p>
        </div>
        
        <div class="content">
            <div class="cost-summary">
                <h3>💰 Cost Overview</h3>
                <p>Here's what you can expect to pay for DOTM services:</p>
                <div class="cost-grid">
                    <div class="cost-item">
                        <h4>Free Tier</h4>
                        <div class="price">${{ "%.2f"|format(costs.minimum_monthly) }}/mo</div>
                        <small>Beta access only</small>
                    </div>
                    <div class="cost-item">
                        <h4>Basic Plan</h4>
                        <div class="price">${{ "%.2f"|format(costs.basic_yearly) }}/year</div>
                        <small>Core connectivity</small>
                    </div>
                    <div class="cost-item">
                        <h4>Full Plan</h4>
                        <div class="price">${{ "%.2f"|format(costs.full_yearly) }}/year</div>
                        <small>Premium features</small>
                    </div>
                    <div class="cost-item">
                        <h4>Maximum</h4>
                        <div class="price">${{ "%.2f"|format(costs.maximum_monthly) }}/mo</div>
                        <small>All add-ons included</small>
                    </div>
                </div>
            </div>

            {% for category_id, category in services.items() %}
            <div class="service-category">
                <div class="category-header">
                    <h2>{{ category.title }}</h2>
                    <p>{{ category.description }}</p>
                </div>
                <div class="services-grid">
                    {% for service in category.services %}
                    <div class="service-item">
                        <div class="service-header">
                            <div class="service-info">
                                <h3>{{ service.name }}</h3>
                                <p>{{ service.description }}</p>
                            </div>
                            <div class="service-pricing">
                                {% if service.price_usd == 0.00 %}
                                    <div class="price-main">FREE</div>
                                {% else %}
                                    <div class="price-main">${{ "%.2f"|format(service.price_usd) }}</div>
                                {% endif %}
                                {% if service.get('billing_cycle') %}
                                    <div class="price-cycle">{{ service.billing_cycle }}</div>
                                {% endif %}
                                {% if service.get('processing_fee') %}
                                    <div class="price-cycle">+ {{ service.processing_fee }}</div>
                                {% endif %}
                                {% if service.get('token_amount') %}
                                    <div class="price-cycle">{{ service.token_amount }}</div>
                                {% endif %}
                                {% if service.get('reward_percentage') %}
                                    <div class="price-cycle">{{ service.reward_percentage }} back</div>
                                {% endif %}
                            </div>
                        </div>
                        
                        <div class="features">
                            <ul>
                                {% for feature in service.features %}
                                <li>{{ feature }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        
                        <div class="availability 
                            {%- if service.availability == 'Available' %} available
                            {%- elif 'Beta' in service.availability %} beta
                            {%- elif 'Invitation' in service.availability %} invitation
                            {%- elif 'Limited' in service.availability %} limited
                            {%- elif 'Members' in service.availability %} members
                            {%- else %} available
                            {%- endif %}">
                            {{ service.availability }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}

            <div class="mcp-info">
                <h3>🔌 MCP Server Information</h3>
                <p>This MCP (Model Context Protocol) server provides detailed service information for AI assistants and automated systems.</p>
                
                <div class="api-endpoint">
                    <strong>JSON API:</strong> GET {{ request.url_root }}mcp/api
                </div>
                <div class="api-endpoint">
                    <strong>Service Details:</strong> GET {{ request.url_root }}mcp/service/{service_id}
                </div>
                <div class="api-endpoint">
                    <strong>Pricing Calculator:</strong> GET {{ request.url_root }}mcp/calculate
                </div>
                
                <p><strong>Last Updated:</strong> {{ timestamp }}</p>
                <p><strong>Total Services:</strong> {{ total_services }} across {{ total_categories }} categories</p>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    total_services = sum(len(category["services"]) for category in SERVICES_CATALOG.values())
    total_categories = len(SERVICES_CATALOG)
    
    return render_template_string(
        mcp_template,
        services=SERVICES_CATALOG,
        costs=costs,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        total_services=total_services,
        total_categories=total_categories
    )

def mcp_api():
    """JSON API endpoint for programmatic access"""
    return jsonify({
        "platform": "DOTM",
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "services": SERVICES_CATALOG,
        "cost_summary": calculate_total_costs(),
        "endpoints": {
            "service_details": "/mcp/service/{service_id}",
            "pricing_calculator": "/mcp/calculate",
            "full_catalog": "/mcp"
        }
    })

def mcp_service_detail(service_id):
    """Get details for a specific service"""
    for category in SERVICES_CATALOG.values():
        for service in category["services"]:
            if service["id"] == service_id:
                return jsonify({
                    "service": service,
                    "category": category["title"],
                    "timestamp": datetime.now().isoformat()
                })
    
    return jsonify({"error": "Service not found"}), 404

def mcp_pricing_calculator():
    """Calculate pricing based on selected services"""
    from flask import request
    
    selected_services = request.args.getlist('services')
    if not selected_services:
        return jsonify({
            "error": "No services specified",
            "usage": "Add ?services=service_id1,service_id2 to calculate pricing"
        })
    
    total_cost = 0
    monthly_cost = 0
    yearly_cost = 0
    selected_details = []
    
    for category in SERVICES_CATALOG.values():
        for service in category["services"]:
            if service["id"] in selected_services:
                selected_details.append(service)
                
                if service["type"] in ["one_time_purchase", "one_time_reward"]:
                    total_cost += service["price_usd"]
                elif service["type"] == "monthly_subscription" or service.get("billing_cycle") == "monthly":
                    monthly_cost += service["price_usd"]
                elif service["type"] == "annual_subscription" or service.get("billing_cycle") == "yearly":
                    yearly_cost += service["price_usd"]
                    monthly_cost += service["price_usd"] / 12
    
    return jsonify({
        "selected_services": selected_details,
        "pricing": {
            "one_time_total": total_cost,
            "monthly_recurring": monthly_cost,
            "yearly_recurring": yearly_cost,
            "first_year_total": total_cost + yearly_cost + (monthly_cost * 12)
        },
        "timestamp": datetime.now().isoformat()
    })

# Functions are now imported and used by main.py
