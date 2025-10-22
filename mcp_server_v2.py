#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for DOTM Platform
Version 2.0 - Following MCP 2025 Specification (2025-06-18)

This server exposes DOTM services, pricing, and capabilities through the
standardized Model Context Protocol, enabling AI assistants to access
structured service information programmatically.

Specification: https://modelcontextprotocol.io/specification/2025-06-18
Transport: HTTP + SSE (Streamable HTTP)
Protocol: JSON-RPC 2.0
"""

from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime, timedelta
import json
import logging
import os
import asyncio
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from mcp.server.models import InitializationOptions

from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware

from firebase_helper import verify_firebase_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                "price_usd": 20.00,
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
                "price_usd": 24.00,
                "billing_cycle": "yearly",
                "features": [
                    "Global data access",
                    "$1 per GB of data bonus - limited availability",
                    "2FA support via incoming SMS only",
                    "eSIM line activation included",
                    "Unlimited Hotspot",
                    "Infinite data share with any member"
                ],
                "availability": "Available"
            },
            {
                "id": "full_membership",
                "name": "Full Membership",
                "description": "Unlimited Talk + Text, Global Wi-Fi Calling",
                "type": "annual_subscription",
                "price_usd": 66.00,
                "billing_cycle": "yearly",
                "features": [
                    "Unlimited talk and text in North America",
                    "Wi-Fi Calling access globally",
                    "Satellite D2C (Available in 2026)"
                ],
                "availability": "Available"
            }
        ]
    },
    "network_features": {
        "title": "Network Features",
        "description": "Advanced network capabilities and optimizations",
        "services": [
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
                    "No-logs policy"
                ],
                "availability": "Available"
            },
            {
                "id": "network_security_basic",
                "name": "Network Security",
                "description": "Basic network security features",
                "type": "add_on",
                "price_usd": 5.00,
                "billing_cycle": "monthly",
                "features": [
                    "Firewall protection",
                    "Threat detection",
                    "Basic DDoS protection"
                ],
                "availability": "Available"
            }
        ]
    }
}


class MCPAuthMiddleware:
    """Authentication middleware for MCP server with auto-registration"""
    
    def __init__(self):
        self.registered_users = {}
    
    async def authenticate(self, authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with Firebase token and auto-register if new
        Returns user info or None if authentication fails
        """
        if not authorization:
            logger.warning("No authorization header provided")
            return None
        
        if not authorization.startswith('Bearer '):
            logger.warning("Invalid authorization header format")
            return None
        
        token = authorization.split('Bearer ')[1]
        
        try:
            class MockRequest:
                def __init__(self, token):
                    self.headers = {'Authorization': f'Bearer {token}'}
            
            mock_request = MockRequest(token)
            decoded_token, error = verify_firebase_token(mock_request)
            
            if error:
                logger.warning(f"Token verification failed: {error}")
                return None
            
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email', 'unknown@example.com')
            
            if firebase_uid not in self.registered_users:
                logger.info(f"Auto-registering new user: {firebase_uid}")
                self.registered_users[firebase_uid] = {
                    'firebase_uid': firebase_uid,
                    'email': email,
                    'registered_at': datetime.now().isoformat(),
                    'name': decoded_token.get('name', email.split('@')[0])
                }
            
            user_info = self.registered_users[firebase_uid]
            logger.info(f"Authenticated user: {user_info['email']}")
            return user_info
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None


class MCPDOTMServer:
    """Model Context Protocol Server for DOTM Platform"""
    
    def __init__(self):
        self.server = Server("dotm-mcp-server")
        self.auth_middleware = MCPAuthMiddleware()
        
        # Store handler references for Flask endpoint access
        self.handlers = {}
        
        self._register_resources()
        self._register_tools()
        self._register_prompts()
        logger.info("DOTM MCP Server initialized")
    
    def _register_resources(self):
        """Register MCP Resources - read-only data access"""
        
        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List all available resources"""
            return [
                types.Resource(
                    uri="dotm://services/catalog",
                    name="Complete Service Catalog",
                    description="Full catalog of DOTM services, pricing, and features",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="dotm://services/membership",
                    name="Membership Plans",
                    description="Annual subscription plans with benefits",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="dotm://services/network",
                    name="Network Features",
                    description="Advanced network capabilities and add-ons",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="dotm://pricing/summary",
                    name="Pricing Summary",
                    description="Cost overview and pricing calculations",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read specific resource content"""
            logger.info(f"Reading resource: {uri}")
            
            if uri == "dotm://services/catalog":
                return json.dumps(SERVICES_CATALOG, indent=2)
            
            elif uri == "dotm://services/membership":
                return json.dumps(SERVICES_CATALOG["membership_plans"], indent=2)
            
            elif uri == "dotm://services/network":
                return json.dumps(SERVICES_CATALOG["network_features"], indent=2)
            
            elif uri == "dotm://pricing/summary":
                costs = self._calculate_costs()
                return json.dumps(costs, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        # Store handlers for direct access
        self.handlers['list_resources'] = list_resources
        self.handlers['read_resource'] = read_resource
    
    def _register_tools(self):
        """Register MCP Tools - executable functions"""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List all available tools"""
            return [
                types.Tool(
                    name="calculate_pricing",
                    description="Calculate total pricing for selected services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of service IDs to include in calculation"
                            }
                        },
                        "required": ["service_ids"]
                    }
                ),
                types.Tool(
                    name="search_services",
                    description="Search for services by keyword, type, or availability",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (name, description, features)"
                            },
                            "service_type": {
                                "type": "string",
                                "description": "Filter by type (one_time_purchase, annual_subscription, add_on)",
                                "enum": ["one_time_purchase", "annual_subscription", "add_on", "beta_program"]
                            },
                            "max_price": {
                                "type": "number",
                                "description": "Maximum price in USD"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_service_details",
                    description="Get detailed information about a specific service",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_id": {
                                "type": "string",
                                "description": "Service ID (e.g., basic_membership, network_vpn_access)"
                            }
                        },
                        "required": ["service_id"]
                    }
                ),
                types.Tool(
                    name="compare_memberships",
                    description="Compare different membership plans side-by-side",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Membership plan IDs to compare"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="activate_esim",
                    description="Activate eSIM for authenticated user - processes beta eSIM activation with OXIO integration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "User's email address for eSIM activation and confirmation"
                            },
                            "firebase_uid": {
                                "type": "string",
                                "description": "Firebase UID of authenticated user"
                            }
                        },
                        "required": ["email", "firebase_uid"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Sequence[types.TextContent]:
            """Execute tool functions"""
            logger.info(f"Calling tool: {name} with args: {arguments}")
            
            if name == "calculate_pricing":
                result = await self._calculate_pricing_tool(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "search_services":
                result = await self._search_services_tool(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "get_service_details":
                result = await self._get_service_details_tool(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "compare_memberships":
                result = await self._compare_memberships_tool(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "activate_esim":
                result = await self._activate_esim_tool(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        # Store handlers for direct access
        self.handlers['list_tools'] = list_tools
        self.handlers['call_tool'] = call_tool
    
    def _register_prompts(self):
        """Register MCP Prompts - reusable templates"""
        
        @self.server.list_prompts()
        async def list_prompts() -> List[types.Prompt]:
            """List all available prompts"""
            return [
                types.Prompt(
                    name="recommend_plan",
                    description="Get personalized plan recommendation based on user needs",
                    arguments=[
                        types.PromptArgument(
                            name="usage_pattern",
                            description="User's typical usage (e.g., 'frequent traveler', 'basic user', 'heavy data user')",
                            required=True
                        ),
                        types.PromptArgument(
                            name="budget",
                            description="Monthly budget in USD",
                            required=False
                        )
                    ]
                ),
                types.Prompt(
                    name="explain_service",
                    description="Get detailed explanation of a service in simple terms",
                    arguments=[
                        types.PromptArgument(
                            name="service_id",
                            description="Service ID to explain",
                            required=True
                        )
                    ]
                ),
                types.Prompt(
                    name="cost_optimization",
                    description="Analyze and suggest cost optimization for current services",
                    arguments=[
                        types.PromptArgument(
                            name="current_services",
                            description="Comma-separated list of current service IDs",
                            required=True
                        )
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
            """Get prompt with arguments"""
            logger.info(f"Getting prompt: {name} with args: {arguments}")
            
            if name == "recommend_plan":
                usage = arguments.get("usage_pattern", "basic user")
                budget = arguments.get("budget", "flexible")
                
                prompt_text = f"""Based on the user profile:
- Usage Pattern: {usage}
- Budget: {budget}

Analyze the DOTM service catalog and recommend the best membership plan and add-ons.
Consider cost-effectiveness, features alignment, and long-term value.

Please provide:
1. Recommended membership plan (Basic or Full)
2. Suggested add-ons (if any)
3. Total estimated cost (monthly and yearly)
4. Reasoning for each recommendation
"""
                return types.GetPromptResult(
                    description=f"Plan recommendation for {usage}",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(type="text", text=prompt_text)
                        )
                    ]
                )
            
            elif name == "explain_service":
                service_id = arguments.get("service_id")
                service = self._find_service_by_id(service_id)
                
                if not service:
                    raise ValueError(f"Service not found: {service_id}")
                
                prompt_text = f"""Explain this DOTM service in simple, everyday language:

Service: {service['name']}
Price: ${service['price_usd']}
Type: {service['type']}

Features:
{chr(10).join('- ' + f for f in service['features'])}

Provide a clear explanation that a non-technical user would understand, including:
1. What this service does
2. Who would benefit from it
3. How it compares to similar services
4. Any important considerations
"""
                return types.GetPromptResult(
                    description=f"Explanation of {service['name']}",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(type="text", text=prompt_text)
                        )
                    ]
                )
            
            elif name == "cost_optimization":
                service_ids = arguments.get("current_services", "").split(",")
                service_ids = [s.strip() for s in service_ids if s.strip()]
                
                current_services = [self._find_service_by_id(sid) for sid in service_ids]
                current_services = [s for s in current_services if s]
                
                total_cost = sum(s['price_usd'] for s in current_services)
                
                services_list = "\n".join(f"- {s['name']}: ${s['price_usd']}" for s in current_services)
                
                prompt_text = f"""Current DOTM Services:
{services_list}

Total Current Cost: ${total_cost}

Analyze these services and suggest:
1. Any redundant or overlapping services
2. More cost-effective alternatives
3. Services that could be bundled
4. Potential savings opportunities
5. Recommended optimized service set

Provide specific actionable recommendations with cost savings calculations.
"""
                return types.GetPromptResult(
                    description="Cost optimization analysis",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(type="text", text=prompt_text)
                        )
                    ]
                )
            
            else:
                raise ValueError(f"Unknown prompt: {name}")
        
        # Store handlers for direct access
        self.handlers['list_prompts'] = list_prompts
        self.handlers['get_prompt'] = get_prompt
    
    async def _calculate_pricing_tool(self, args: dict) -> dict:
        """Calculate pricing for selected services"""
        service_ids = args.get("service_ids", [])
        
        total_one_time = 0.0
        total_monthly = 0.0
        total_yearly = 0.0
        selected_services = []
        
        for category in SERVICES_CATALOG.values():
            for service in category["services"]:
                if service["id"] in service_ids:
                    selected_services.append(service)
                    price = service["price_usd"]
                    
                    if service["type"] in ["one_time_purchase", "one_time_reward"]:
                        total_one_time += price
                    elif service.get("billing_cycle") == "monthly" or service["type"] == "monthly_subscription":
                        total_monthly += price
                    elif service.get("billing_cycle") == "yearly" or service["type"] == "annual_subscription":
                        total_yearly += price
                        total_monthly += price / 12
        
        return {
            "selected_services": selected_services,
            "pricing": {
                "one_time_total_usd": round(total_one_time, 2),
                "monthly_recurring_usd": round(total_monthly, 2),
                "yearly_recurring_usd": round(total_yearly, 2),
                "first_year_total_usd": round(total_one_time + total_yearly + (total_monthly * 12), 2)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _search_services_tool(self, args: dict) -> dict:
        """Search services by query, type, and price"""
        query = args.get("query", "").lower()
        service_type = args.get("service_type")
        max_price = args.get("max_price")
        
        results = []
        
        for category_id, category in SERVICES_CATALOG.items():
            for service in category["services"]:
                if query and query not in service["name"].lower() and \
                   query not in service["description"].lower() and \
                   not any(query in f.lower() for f in service.get("features", [])):
                    continue
                
                if service_type and service["type"] != service_type:
                    continue
                
                if max_price is not None and service["price_usd"] > max_price:
                    continue
                
                results.append({
                    **service,
                    "category": category["title"]
                })
        
        return {
            "query": query,
            "filters": {
                "service_type": service_type,
                "max_price": max_price
            },
            "results_count": len(results),
            "results": results
        }
    
    async def _get_service_details_tool(self, args: dict) -> dict:
        """Get detailed service information"""
        service_id = args.get("service_id", "")
        
        if not service_id:
            return {"error": "service_id is required"}
        
        for category_id, category in SERVICES_CATALOG.items():
            for service in category["services"]:
                if service["id"] == service_id:
                    return {
                        "service": service,
                        "category": category["title"],
                        "category_id": category_id,
                        "timestamp": datetime.now().isoformat()
                    }
        
        return {"error": f"Service not found: {service_id}"}
    
    async def _compare_memberships_tool(self, args: dict) -> dict:
        """Compare membership plans"""
        plan_ids = args.get("plan_ids", ["basic_membership", "full_membership"])
        
        plans = []
        for service in SERVICES_CATALOG["membership_plans"]["services"]:
            if service["id"] in plan_ids or not plan_ids:
                plans.append(service)
        
        return {
            "comparison": {
                "plans": plans,
                "price_difference_usd": abs(plans[0]["price_usd"] - plans[1]["price_usd"]) if len(plans) == 2 else 0,
                "monthly_equivalent": [
                    {
                        "plan": p["name"],
                        "monthly_usd": round(p["price_usd"] / 12, 2)
                    } for p in plans
                ]
            }
        }
    
    async def _activate_esim_tool(self, args: dict) -> dict:
        """Activate eSIM for authenticated user via OXIO integration"""
        email = args.get("email", "")
        firebase_uid = args.get("firebase_uid", "")
        
        if not email or not firebase_uid:
            return {
                "success": False,
                "error": "Missing required fields",
                "message": "Both email and firebase_uid are required for eSIM activation"
            }
        
        try:
            # Import required functions from main.py
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from main import activate_esim_for_user, get_user_by_firebase_uid, get_db_connection
            
            # Check if user exists, if not create them
            user_data = get_user_by_firebase_uid(firebase_uid)
            if not user_data:
                # User doesn't exist - create new user with ChatGPT/Gemini provided email
                logger.info(f"Creating new user from AI assistant: {firebase_uid} / {email}")
                
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            # Insert new user into users table
                            cur.execute("""
                                INSERT INTO users (firebase_uid, email, created_at)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                RETURNING id, firebase_uid, email
                            """, (firebase_uid, email))
                            
                            new_user = cur.fetchone()
                            conn.commit()
                            
                            if new_user:
                                user_id, uid, user_email = new_user
                                logger.info(f"Created new user from AI: ID {user_id}, UID {uid}, Email {user_email}")
                                user_data = {
                                    'id': user_id,
                                    'firebase_uid': uid,
                                    'email': user_email,
                                    'created_via_ai': True
                                }
                            else:
                                logger.error("Failed to create user - no data returned")
                                return {
                                    "success": False,
                                    "error": "User creation failed",
                                    "message": "Unable to create user account. Please try again."
                                }
                        
                except Exception as db_error:
                    logger.error(f"Error creating user: {str(db_error)}")
                    return {
                        "success": False,
                        "error": "User creation failed",
                        "message": f"Error creating user account: {str(db_error)}"
                    }
            
            # Verify email matches (important for existing users)
            if user_data.get('email') != email:
                logger.warning(f"Email mismatch for {firebase_uid}: expected {user_data.get('email')}, got {email}")
                return {
                    "success": False,
                    "error": "Email mismatch",
                    "message": f"The email {email} doesn't match your registered email. Please use your registered email address."
                }
            
            # Check if user has paid for eSIM beta
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        # Check for eSIM beta purchase
                        cur.execute("""
                            SELECT PurchaseID, DateCreated, StripeTransactionID 
                            FROM purchases 
                            WHERE FirebaseUID = %s 
                            AND StripeProductID = 'esim_beta'
                            ORDER BY DateCreated DESC 
                            LIMIT 1
                        """, (firebase_uid,))
                        
                        purchase = cur.fetchone()
                        
                        if not purchase:
                            # No payment found - send Stripe invoice
                            logger.info(f"No payment found for {firebase_uid} - creating Stripe invoice")
                            
                            try:
                                import stripe
                                import os
                                stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
                                
                                # Create or get Stripe customer
                                customers = stripe.Customer.list(email=email, limit=1)
                                if customers.data:
                                    customer = customers.data[0]
                                else:
                                    customer = stripe.Customer.create(
                                        email=email,
                                        metadata={'firebase_uid': firebase_uid}
                                    )
                                
                                # Create invoice item for eSIM beta ($1)
                                stripe.InvoiceItem.create(
                                    customer=customer.id,
                                    price='price_1S7Yc6JnTfh0bNQQVeLeprXe',  # eSIM beta price ID
                                    metadata={
                                        'firebaseUid': firebase_uid,
                                        'product': 'esim_beta',
                                        'source': 'mcp_v2_activation'
                                    }
                                )
                                
                                # Create and send the invoice
                                invoice = stripe.Invoice.create(
                                    customer=customer.id,
                                    auto_advance=True,
                                    collection_method='send_invoice',
                                    days_until_due=7,
                                    metadata={
                                        'firebaseUid': firebase_uid,
                                        'product': 'esim_beta'
                                    }
                                )
                                
                                # Finalize and send the invoice
                                invoice = stripe.Invoice.finalize_invoice(invoice.id)
                                sent_invoice = stripe.Invoice.send_invoice(invoice.id)
                                
                                logger.info(f"Stripe invoice sent to {email}: {invoice.id}")
                                
                                return {
                                    "success": False,
                                    "status": "invoice_sent",
                                    "message": f"I've sent a $1 invoice to {email} for eSIM activation. Please check your email and pay the invoice, then ask me to activate again.",
                                    "invoice_url": invoice.hosted_invoice_url,
                                    "invoice_id": invoice.id,
                                    "amount_due": 1.00,
                                    "next_steps": [
                                        f"Check {email} for the Stripe invoice",
                                        "Pay the $1 invoice",
                                        "Come back and say 'activate my eSIM' again"
                                    ]
                                }
                                
                            except Exception as stripe_error:
                                logger.error(f"Failed to create Stripe invoice: {str(stripe_error)}")
                                return {
                                    "success": False,
                                    "error": "Invoice creation failed",
                                    "message": f"Unable to send invoice. Please contact support. Error: {str(stripe_error)}"
                                }
                        
                        purchase_id, purchase_date, transaction_id = purchase
                        logger.info(f"Verified eSIM beta purchase: {purchase_id} for user {firebase_uid}")
                        
                finally:
                    conn.close()
            else:
                logger.warning("Database connection failed - proceeding without payment verification")
            
            # Create a mock checkout session for compatibility with activate_esim_for_user
            mock_session = {
                'id': f'mcp_activation_{firebase_uid}_{int(datetime.now().timestamp())}',
                'customer_email': email,
                'metadata': {
                    'firebaseUid': firebase_uid,
                    'source': 'mcp_v2_server',
                    'ai_assistant': 'chatgpt_or_gemini'
                }
            }
            
            # Call the activation function
            logger.info(f"Activating eSIM for user {firebase_uid} via MCP v2 server")
            result = activate_esim_for_user(firebase_uid, mock_session)
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": "eSIM activation successful!",
                    "details": {
                        "email": email,
                        "phone_number": result.get('phone_number', 'Assigned by carrier'),
                        "plan": "OXIO Base Plan (Basic Membership)",
                        "status": "Active",
                        "activation_id": result.get('line_id', 'N/A'),
                        "purchase_verified": True
                    },
                    "next_steps": [
                        "Check your email for eSIM activation details and QR code",
                        "Log into your DOTM dashboard to view your phone number",
                        "Scan the QR code with your device to activate eSIM"
                    ]
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Unknown error'),
                    "message": result.get('message', 'eSIM activation failed')
                }
                
        except Exception as e:
            logger.error(f"Error in activate_esim tool: {str(e)}")
            return {
                "success": False,
                "error": "Activation error",
                "message": f"An error occurred during eSIM activation: {str(e)}"
            }
    
    def _calculate_costs(self) -> dict:
        """Calculate cost overview"""
        costs = {
            "minimum_monthly_usd": 0.00,
            "basic_monthly_usd": 2.00,
            "full_monthly_usd": 5.50,
            "maximum_monthly_usd": 0.00
        }
        
        network_addons = SERVICES_CATALOG["network_features"]["services"]
        max_addon_cost = sum(s["price_usd"] for s in network_addons if s["price_usd"] > 0)
        
        costs["maximum_monthly_usd"] = costs["full_monthly_usd"] + max_addon_cost
        costs["basic_yearly_usd"] = 24.00
        costs["full_yearly_usd"] = 66.00
        costs["maximum_yearly_usd"] = costs["maximum_monthly_usd"] * 12
        
        return costs
    
    def _find_service_by_id(self, service_id: str) -> Optional[dict]:
        """Find service by ID across all categories"""
        for category in SERVICES_CATALOG.values():
            for service in category["services"]:
                if service["id"] == service_id:
                    return service
        return None


mcp_server = MCPDOTMServer()
auth_middleware = MCPAuthMiddleware()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    logger.info("Starting DOTM MCP Server")
    yield
    logger.info("Shutting down DOTM MCP Server")


app = FastAPI(
    title="DOTM MCP Server",
    description="Model Context Protocol Server for DOTM Platform Services",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency for user authentication"""
    user = await auth_middleware.authenticate(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@app.get("/mcp/v2")
async def mcp_info():
    """MCP server information endpoint"""
    return {
        "server": "DOTM MCP Server",
        "version": "2.0.0",
        "protocol_version": "2024-11-05",
        "specification": "https://modelcontextprotocol.io/specification/2024-11-05",
        "transport": "HTTP + SSE (Streamable HTTP)",
        "capabilities": {
            "resources": {
                "subscribe": False,
                "listChanged": True
            },
            "tools": {
                "listChanged": True
            },
            "prompts": {
                "listChanged": False
            }
        },
        "endpoints": {
            "sse": "/mcp/v2/sse",
            "messages": "/mcp/v2/messages",
            "info": "/mcp/v2",
            "docs": "/mcp/v2/docs"
        },
        "authentication": {
            "type": "Firebase Bearer Token",
            "auto_registration": True,
            "required": False
        }
    }


@app.get("/mcp/v2/sse")
async def sse_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    """Server-Sent Events endpoint for server-to-client streaming"""
    
    user = await auth_middleware.authenticate(authorization) if authorization else None
    
    async def event_generator():
        yield {
            "event": "endpoint",
            "data": json.dumps({
                "endpoint": "/mcp/v2/messages",
                "protocol_version": "2024-11-05",
                "authenticated": user is not None,
                "user": user["email"] if user else "anonymous"
            })
        }
        
        while True:
            if await request.is_disconnected():
                logger.info("SSE client disconnected")
                break
            
            yield {
                "event": "ping",
                "data": json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "status": "connected"
                })
            }
            
            await asyncio.sleep(30)
    
    return EventSourceResponse(event_generator())


@app.post("/mcp/v2/messages")
async def messages_endpoint(request: Request):
    """JSON-RPC 2.0 endpoint for client-to-server requests"""
    try:
        body = await request.json()
        logger.info(f"Received JSON-RPC request: {body.get('method')}")
        
        if body.get("jsonrpc") != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: jsonrpc must be '2.0'"
                }
            }, status_code=400)
        
        method = body.get("method")
        msg_id = body.get("id")
        params = body.get("params", {})
        
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "resources": {"subscribe": False, "listChanged": True},
                        "tools": {"listChanged": True},
                        "prompts": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "dotm-mcp-server",
                        "version": "2.0.0"
                    }
                }
            })
        
        elif method == "resources/list":
            resources = await mcp_server.server._resource_manager.list_resources()
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "resources": [
                        {
                            "uri": r.uri,
                            "name": r.name,
                            "description": r.description,
                            "mimeType": r.mimeType
                        } for r in resources
                    ]
                }
            })
        
        elif method == "resources/read":
            uri = params.get("uri")
            content = await mcp_server.server._resource_manager.read_resource(uri)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content
                    }]
                }
            })
        
        elif method == "tools/list":
            tools = await mcp_server.server._tool_manager.list_tools()
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "inputSchema": t.inputSchema
                        } for t in tools
                    ]
                }
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            content = await mcp_server.server._tool_manager.call_tool(tool_name, arguments)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": c.type, "text": c.text} for c in content
                    ]
                }
            })
        
        elif method == "prompts/list":
            prompts = await mcp_server.server._prompt_manager.list_prompts()
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "prompts": [
                        {
                            "name": p.name,
                            "description": p.description,
                            "arguments": [
                                {
                                    "name": a.name,
                                    "description": a.description,
                                    "required": a.required
                                } for a in (p.arguments or [])
                            ]
                        } for p in prompts
                    ]
                }
            })
        
        elif method == "prompts/get":
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await mcp_server.server._prompt_manager.get_prompt(prompt_name, arguments)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "description": result.description,
                    "messages": [
                        {
                            "role": m.role,
                            "content": {"type": m.content.type, "text": m.content.text}
                        } for m in result.messages
                    ]
                }
            })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, status_code=500)


@app.get("/mcp/v2/docs")
async def api_docs():
    """Comprehensive API documentation"""
    return {
        "title": "DOTM MCP Server API Documentation",
        "version": "2.0.0",
        "protocol": "Model Context Protocol (MCP) 2024-11-05",
        "base_url": "/mcp/v2",
        
        "authentication": {
            "type": "Firebase Bearer Token",
            "header": "Authorization: Bearer <firebase_token>",
            "auto_registration": True,
            "optional": True,
            "description": "Authentication is optional for read-only operations. Required for user-specific features."
        },
        
        "endpoints": {
            "GET /mcp/v2": {
                "description": "Server information and capabilities",
                "authentication": "Optional",
                "response": "Server metadata and endpoint URLs"
            },
            "GET /mcp/v2/sse": {
                "description": "Server-Sent Events for real-time updates",
                "authentication": "Optional",
                "transport": "SSE",
                "content_type": "text/event-stream"
            },
            "POST /mcp/v2/messages": {
                "description": "JSON-RPC 2.0 endpoint for all MCP operations",
                "authentication": "Optional",
                "content_type": "application/json",
                "methods": [
                    "initialize",
                    "resources/list",
                    "resources/read",
                    "tools/list",
                    "tools/call",
                    "prompts/list",
                    "prompts/get"
                ]
            },
            "GET /mcp/v2/docs": {
                "description": "This documentation endpoint",
                "authentication": "None"
            }
        },
        
        "resources": [
            {
                "uri": "dotm://services/catalog",
                "name": "Complete Service Catalog",
                "description": "Full catalog of all DOTM services"
            },
            {
                "uri": "dotm://services/membership",
                "name": "Membership Plans",
                "description": "Annual subscription plans"
            },
            {
                "uri": "dotm://services/network",
                "name": "Network Features",
                "description": "Network add-ons and features"
            },
            {
                "uri": "dotm://pricing/summary",
                "name": "Pricing Summary",
                "description": "Cost overview calculations"
            }
        ],
        
        "tools": [
            {
                "name": "calculate_pricing",
                "description": "Calculate total pricing for selected services",
                "input": {"service_ids": ["array of service IDs"]}
            },
            {
                "name": "search_services",
                "description": "Search services by keyword, type, or price",
                "input": {"query": "string", "service_type": "optional", "max_price": "optional"}
            },
            {
                "name": "get_service_details",
                "description": "Get detailed information about a specific service",
                "input": {"service_id": "string"}
            },
            {
                "name": "compare_memberships",
                "description": "Compare membership plans side-by-side",
                "input": {"plan_ids": ["optional array of plan IDs"]}
            }
        ],
        
        "prompts": [
            {
                "name": "recommend_plan",
                "description": "Get personalized plan recommendation",
                "arguments": ["usage_pattern", "budget (optional)"]
            },
            {
                "name": "explain_service",
                "description": "Get detailed service explanation",
                "arguments": ["service_id"]
            },
            {
                "name": "cost_optimization",
                "description": "Analyze and optimize service costs",
                "arguments": ["current_services"]
            }
        ],
        
        "examples": {
            "initialize": {
                "request": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "client", "version": "1.0.0"}
                    }
                }
            },
            "list_tools": {
                "request": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
            },
            "calculate_pricing": {
                "request": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_pricing",
                        "arguments": {
                            "service_ids": ["basic_membership", "network_vpn_access"]
                        }
                    }
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
