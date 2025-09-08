
# DOTM Platform Deployment Guide

## Overview

This guide covers the deployment of the DOTM Platform to GitHub and various hosting environments.

## GitHub Repository Structure

```
dotm-platform/
├── docs/                      # Documentation
│   ├── README_MCP.md         # MCP Server documentation
│   ├── MCP_API_REFERENCE.md  # Complete API reference
│   ├── ARCHITECTURE.md       # System architecture
│   ├── DEPLOYMENT.md         # This file
│   └── CONTRIBUTING.md       # Contribution guidelines
├── src/                      # Source code
│   ├── main.py              # Main application
│   ├── mcp_server.py        # MCP server implementation
│   ├── oxio_service.py      # OXIO integration
│   └── stripe_products.py   # Payment processing
├── static/                   # Static assets
├── templates/               # HTML templates
├── requirements.txt         # Python dependencies
└── README.md               # Main project README
```

## Live Deployments

### Production URLs
- **Main Platform**: `https://get-dot-esim.replit.app`
- **MCP Server**: `https://get-dot-esim.replit.app/mcp`
- **Alternative MCP**: `https://mcp.dotmobile.app`

### API Endpoints
- **Interactive Interface**: `GET /mcp`
- **JSON API**: `GET /mcp/api`
- **Service Details**: `GET /mcp/service/{service_id}`
- **Pricing Calculator**: `GET /mcp/calculate`

## Deployment Instructions

### 1. GitHub Repository Setup

```bash
# Create new repository
git init
git add .
git commit -m "Initial DOTM Platform documentation"
git remote add origin https://github.com/username/dotm-platform.git
git push -u origin main
```

### 2. Documentation Publishing

The documentation is automatically published via GitHub Actions:

```yaml
# .github/workflows/publish-docs.yml
name: Publish Documentation
on:
  push:
    branches: [ main ]
    paths: [ 'docs/**' ]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

### 3. Environment Variables

```bash
# Required environment variables
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_firebase_domain
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
OXIO_API_KEY=your_oxio_api_key
DATABASE_URL=postgresql://...
```

## MCP Server Deployment

### Replit Deployment (Current)
The MCP server is currently deployed on Replit with the following configuration:

```python
# Flask configuration for Replit
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Custom Domain Setup
For `mcp.dotmobile.app`:

1. Configure DNS CNAME record
2. Set up SSL certificate
3. Update routing configuration

## API Documentation Deployment

### GitHub Pages Setup
1. Enable GitHub Pages in repository settings
2. Select source: GitHub Actions
3. Documentation will be available at: `https://username.github.io/dotm-platform`

### Custom Domain Configuration
```
# CNAME file in docs directory
docs.dotmobile.app
```

## Monitoring & Analytics

### Health Checks
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': check_database_health(),
            'stripe': check_stripe_health(),
            'oxio': check_oxio_health()
        }
    }
```

### Performance Monitoring
- **Response Times**: Track API endpoint performance
- **Error Rates**: Monitor application errors
- **Usage Metrics**: Track service adoption
- **Cost Analysis**: Monitor infrastructure costs

## Security Considerations

### SSL/TLS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name mcp.dotmobile.app;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### API Security
- **Rate Limiting**: 100 requests per minute per IP
- **CORS Configuration**: Restricted to allowed domains
- **Input Validation**: All parameters validated
- **Error Handling**: Generic error responses

## Backup & Recovery

### Database Backups
```bash
# Daily automated backups
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Configuration Backups
- Environment variables stored securely
- Service configurations versioned in Git
- SSL certificates backed up

## Update Procedures

### Rolling Updates
1. Deploy new version to staging
2. Run integration tests
3. Deploy to production with zero downtime
4. Monitor for issues
5. Rollback if necessary

### Documentation Updates
1. Update documentation files
2. Commit changes to Git
3. GitHub Actions automatically publishes
4. Verify updates on documentation site

## Support & Maintenance

### Monitoring Tools
- **Uptime Monitoring**: 24/7 service availability checks
- **Performance Metrics**: Response time and throughput
- **Error Tracking**: Automated error reporting
- **Usage Analytics**: Service adoption metrics

### Maintenance Windows
- **Scheduled Maintenance**: Monthly updates
- **Emergency Patches**: As needed
- **Database Maintenance**: Weekly optimization
- **Security Updates**: Immediate deployment

---

*This deployment guide ensures consistent and reliable deployment of the DOTM Platform ecosystem.*
