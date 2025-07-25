
# MCP Server Rules and Guidelines

## PRIVACY AND DATA PROTECTION - MANDATORY COMPLIANCE

### 🔒 ABSOLUTE PRIVACY RULES
- **NEVER** share, display, or reference any end-user private information
- **NEVER** expose user emails, phone numbers, addresses, or personal identifiers
- **NEVER** show Firebase UIDs, Stripe customer IDs, or internal user IDs
- **NEVER** display payment information, credit card details, or financial data
- **NEVER** reveal user activity logs, usage patterns, or behavioral data
- **NEVER** show user passwords, tokens, or authentication credentials

### 📊 PERMISSIBLE INFORMATION ONLY
The MCP server may ONLY provide:
- **Service catalog information** (pricing, features, availability)
- **Product descriptions** and specifications
- **General pricing tiers** and subscription options
- **Feature comparisons** between service levels
- **Technical capabilities** of the platform
- **Public API documentation** and endpoints
- **Support contact information** (public channels only)

### 🚫 FORBIDDEN DATA EXPOSURE
Never expose or reference:
- User account details
- Purchase history or transaction records
- Usage statistics or analytics
- Internal system metrics with user correlation
- Database queries containing personal data
- API responses with user-specific information
- Authentication states or session data
- Network usage patterns or location data

## SERVICE INFORMATION GUIDELINES

### ✅ APPROVED CONTENT
- Service names and descriptions
- Public pricing information
- Feature lists and capabilities
- Availability status (Available, Beta, Limited Edition)
- General subscription terms
- Public support channels
- Technical specifications
- API endpoint documentation (public only)

### ❌ RESTRICTED CONTENT
- Internal service costs or margins
- User adoption rates or statistics
- Revenue information
- Internal system architecture details
- Database schemas or structures
- Server configurations
- Security implementations
- Internal business metrics

## TECHNICAL COMPLIANCE

### Data Handling
- All responses must be static service information
- No dynamic user data retrieval
- No database queries for user-specific information
- No API calls that return personal data
- No logging of user interactions with MCP server

### Error Handling
- Generic error messages only
- No exposure of system internals in errors
- No debug information containing sensitive data
- Graceful degradation without data leakage

### Response Format
- JSON responses for API endpoints
- HTML templates for web interface
- No user data interpolation in templates
- Static content only

## AUDIT AND MONITORING

### Regular Compliance Checks
- Review all MCP endpoints quarterly
- Audit response content for privacy compliance
- Monitor for any accidental data exposure
- Test error conditions for information leakage

### Incident Response
- Immediate shutdown if privacy breach detected
- Review and remediation before restart
- Documentation of any incidents
- User notification if required by law

## IMPLEMENTATION REQUIREMENTS

### Code Standards
- No user data variables in MCP server code
- Static service catalog only
- No database connections for user data
- Sanitized error handling
- Regular security reviews

### Testing Requirements
- Privacy compliance testing for all endpoints
- Automated scanning for sensitive data exposure
- Regular penetration testing
- User privacy simulation tests

## ENFORCEMENT

### Violations
Any violation of these rules requires:
1. Immediate endpoint shutdown
2. Code review and remediation
3. Security team notification
4. Compliance officer approval before restart

### Monitoring
- Automated privacy scanning
- Regular compliance audits
- User privacy advocate reviews
- Legal team oversight

---

**REMEMBER: When in doubt, DO NOT SHARE. The MCP server exists to provide public service information only, never user data.**
