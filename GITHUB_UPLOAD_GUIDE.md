
# GitHub Upload Guide for DOTM Platform Documentation

## Files to Upload

### Core Documentation Files

1. **docs/README.md** - Main documentation index
2. **docs/README_MCP.md** - MCP server comprehensive guide  
3. **docs/MCP_API_REFERENCE.md** - Complete API reference
4. **docs/ARCHITECTURE.md** - System architecture documentation
5. **docs/DEPLOYMENT.md** - Deployment and hosting guide
6. **docs/CONTRIBUTING.md** - Contribution guidelines

### Repository Structure
```
dotm-platform-docs/
├── docs/
│   ├── README.md              # Main documentation hub
│   ├── README_MCP.md          # MCP server documentation
│   ├── MCP_API_REFERENCE.md   # API reference
│   ├── ARCHITECTURE.md        # Architecture guide
│   ├── DEPLOYMENT.md          # Deployment guide
│   └── CONTRIBUTING.md        # Contributing guide
├── .github/
│   └── workflows/
│       └── publish-docs.yml   # GitHub Actions for publishing
├── README.md                  # Repository README
└── LICENSE                    # License file
```

## Upload Instructions

### Step 1: Create GitHub Repository
1. Go to GitHub.com and create new repository
2. Name: `dotm-platform-docs`
3. Description: "Documentation for DOTM Platform MCP Server and Services"
4. Public repository (for GitHub Pages)
5. Initialize with README

### Step 2: Clone and Setup
```bash
git clone https://github.com/yourusername/dotm-platform-docs.git
cd dotm-platform-docs
```

### Step 3: Upload Documentation Files
Copy all the documentation files to the appropriate directories:

- `docs/README.md`
- `docs/README_MCP.md` 
- `docs/MCP_API_REFERENCE.md`
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- `docs/CONTRIBUTING.md`

### Step 4: Commit and Push
```bash
git add .
git commit -m "Add comprehensive DOTM Platform documentation"
git push origin main
```

### Step 5: Enable GitHub Pages
1. Go to repository Settings
2. Scroll to "Pages" section
3. Source: Deploy from a branch
4. Branch: main
5. Folder: /docs
6. Save

## Live URLs

Once uploaded, the documentation will be available at:

### Primary Documentation
- **Main Hub**: `https://yourusername.github.io/dotm-platform-docs/`
- **MCP Server**: `https://yourusername.github.io/dotm-platform-docs/README_MCP`
- **API Reference**: `https://yourusername.github.io/dotm-platform-docs/MCP_API_REFERENCE`
- **Architecture**: `https://yourusername.github.io/dotm-platform-docs/ARCHITECTURE`

### Live Platform URLs (Already Active)
- **MCP Server**: `https://get-dot-esim.replit.app/mcp`
- **MCP API**: `https://get-dot-esim.replit.app/mcp/api`
- **Alternative**: `https://mcp.dotmobile.app`

## Custom Domain Setup (Optional)

### For docs.dotmobile.app
1. Create CNAME file in docs directory:
```
# docs/CNAME
docs.dotmobile.app
```

2. Configure DNS:
```
CNAME docs.dotmobile.app yourusername.github.io
```

## Repository README.md Content

Create a main README.md in the repository root:

```markdown
# DOTM Platform Documentation

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen)](https://yourusername.github.io/dotm-platform-docs/)
[![MCP Server](https://img.shields.io/badge/MCP%20Server-Live-success)](https://get-dot-esim.replit.app/mcp)
[![API Status](https://img.shields.io/badge/API-Operational-success)](https://get-dot-esim.replit.app/mcp/api)

> Comprehensive documentation for the DOTM Platform Model Context Protocol (MCP) Server and global connectivity services.

## 🚀 Quick Access

- **[📚 Documentation Hub](docs/README.md)** - Complete documentation index
- **[🔌 MCP Server Guide](docs/README_MCP.md)** - MCP server features and usage
- **[📖 API Reference](docs/MCP_API_REFERENCE.md)** - Detailed API documentation
- **[🏗️ Architecture](docs/ARCHITECTURE.md)** - System architecture and design

## 🌐 Live Services

- **MCP Server**: [get-dot-esim.replit.app/mcp](https://get-dot-esim.replit.app/mcp)
- **JSON API**: [get-dot-esim.replit.app/mcp/api](https://get-dot-esim.replit.app/mcp/api)
- **Main Platform**: [get-dot-esim.replit.app](https://get-dot-esim.replit.app)

## 📊 Platform Stats

- **20+ Services** across 7 categories
- **Global Coverage** in 190+ countries  
- **99.9% Uptime** for MCP server
- **Real-time Pricing** with dynamic calculations

## 🔧 Quick Start

```bash
# Get all services
curl https://get-dot-esim.replit.app/mcp/api

# Get specific service
curl https://get-dot-esim.replit.app/mcp/service/basic_membership

# Calculate pricing
curl "https://get-dot-esim.replit.app/mcp/calculate?services=basic_membership"
```

## 🤝 Contributing

See our [Contributing Guide](docs/CONTRIBUTING.md) for information on how to contribute to this documentation.

## 📄 License

This documentation is part of the DOTM Platform ecosystem. See LICENSE for details.
```

## Verification Checklist

After upload, verify:

- [ ] All documentation files uploaded correctly
- [ ] GitHub Pages enabled and working
- [ ] All internal links working properly
- [ ] Live MCP server URLs accessible
- [ ] API examples functional
- [ ] Images and assets loading correctly

## Maintenance

### Regular Updates
- Update documentation when MCP server changes
- Add new service examples
- Update pricing information
- Refresh integration guides

### Automated Publishing
The GitHub Actions workflow will automatically publish documentation updates when changes are pushed to the main branch.

---

This guide ensures complete and organized upload of all DOTM Platform documentation to GitHub with proper structure and accessibility.
