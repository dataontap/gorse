
# Contributing to DOTM Platform MCP Documentation

Thank you for your interest in contributing to the DOTM Platform MCP Server documentation!

## How to Contribute

### 1. Documentation Updates
- **API Changes**: Update `docs/MCP_API_REFERENCE.md` when endpoints change
- **Examples**: Add new integration examples to `docs/examples/`
- **Guides**: Improve integration guides in `docs/integration/`

### 2. Code Examples
We welcome examples in any programming language:
- Python (preferred)
- JavaScript/Node.js
- Go
- Rust
- PHP
- Ruby
- C#/.NET

### 3. Integration Guides
- Framework-specific guides (React, Vue, Angular, Django, Flask, etc.)
- Platform integrations (AWS, Azure, GCP)
- Deployment guides
- Performance optimization tips

## Documentation Standards

### File Structure
```
docs/
├── README_MCP.md              # Main documentation
├── api/
│   └── MCP_API_REFERENCE.md   # Complete API reference
├── examples/
│   ├── python_example.py      # Python integration
│   ├── javascript_example.js  # JavaScript integration
│   └── curl_examples.sh       # cURL examples
├── integration/
│   └── README.md              # Integration guide
└── CONTRIBUTING.md            # This file
```

### Writing Style
- Use clear, concise language
- Include code examples for all concepts
- Test all code examples before submitting
- Use consistent formatting and naming conventions

### Code Example Requirements
```python
# ✅ Good: Complete, runnable example
import requests

def get_service_pricing(service_id):
    """Get pricing for a specific service"""
    try:
        response = requests.get(f'https://get-dot-esim.replit.app/mcp/service/{service_id}')
        response.raise_for_status()
        return response.json()['service']['price_usd']
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

# Usage
price = get_service_pricing('basic_membership')
print(f"Basic Membership: ${price}")
```

```python
# ❌ Bad: Incomplete or non-functional
import requests
# ... missing implementation
```

## Testing Your Changes

### 1. Test API Examples
```bash
# Test all endpoints mentioned in documentation
curl https://get-dot-esim.replit.app/mcp/api
curl https://get-dot-esim.replit.app/mcp/service/basic_membership
curl "https://get-dot-esim.replit.app/mcp/calculate?services=basic_membership"
```

### 2. Validate Code Examples
- Python: `python your_example.py`
- JavaScript: `node your_example.js`
- cURL: `bash your_examples.sh`

### 3. Check Documentation Links
- Verify all internal links work
- Test external links to the live MCP server
- Ensure code formatting is correct

## Submission Process

### 1. Create a Pull Request
1. Fork the repository
2. Create a feature branch: `git checkout -b docs/your-improvement`
3. Make your changes
4. Test your changes thoroughly
5. Commit with descriptive messages
6. Push and create a pull request

### 2. Pull Request Guidelines
- **Title**: Clear description of what you're adding/fixing
- **Description**: Explain the changes and why they're needed
- **Testing**: Include evidence that you've tested your changes
- **Breaking Changes**: Note any breaking changes

### Example PR Title and Description
```
Title: Add React integration example for MCP server

Description:
- Added complete React component example for service catalog display
- Includes hooks for data fetching and error handling
- Added TypeScript definitions for MCP API responses
- Tested with React 18 and Next.js 13

Testing:
- Verified example works with create-react-app
- Tested API calls against live MCP server
- Validated TypeScript types
```

## Review Process

### What We Look For
1. **Accuracy**: Information must be correct and up-to-date
2. **Completeness**: Examples should be runnable and complete
3. **Clarity**: Documentation should be easy to understand
4. **Consistency**: Follow existing patterns and style
5. **Testing**: All code examples must be tested

### Review Timeline
- Initial review: 1-3 business days
- Revisions: 1-2 business days after updates
- Final approval: 1 business day

## MCP Server Updates

### When the MCP Server Changes
The documentation automatically updates when:
- New services are added to the catalog
- Pricing changes occur
- New endpoints are added
- Service features are modified

### Keeping Documentation Sync'd
1. Monitor changes to `mcp_server.py`
2. Update API reference when needed
3. Test examples against new API versions
4. Update integration guides for new features

## Recognition

Contributors will be:
- Listed in the documentation credits
- Mentioned in release notes
- Invited to our contributor Discord channel

## Questions?

- Create an issue for documentation questions
- Join our Discord for real-time discussion
- Email support for urgent documentation issues

## Example Contributions

### Adding a New Language Example
```python
# docs/examples/golang_example.go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
)

type MCPService struct {
    ID          string   `json:"id"`
    Name        string   `json:"name"`
    PriceUSD    float64  `json:"price_usd"`
    Features    []string `json:"features"`
}

func getMCPService(serviceID string) (*MCPService, error) {
    url := fmt.Sprintf("https://get-dot-esim.replit.app/mcp/service/%s", serviceID)
    
    resp, err := http.Get(url)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result struct {
        Service MCPService `json:"service"`
    }
    
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return &result.Service, nil
}

func main() {
    service, err := getMCPService("basic_membership")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    fmt.Printf("Service: %s - $%.2f\n", service.Name, service.PriceUSD)
}
```

### Adding Integration Guide
```markdown
# docs/integration/nextjs.md

# Next.js Integration Guide

## Setup

```bash
npm install @types/node
```

## Server-Side Data Fetching

```typescript
// pages/pricing.tsx
import { GetServerSideProps } from 'next'

interface Service {
  id: string
  name: string
  price_usd: number
}

interface Props {
  services: Service[]
}

export default function PricingPage({ services }: Props) {
  return (
    <div>
      <h1>DOTM Services</h1>
      {services.map(service => (
        <div key={service.id}>
          <h3>{service.name}</h3>
          <p>${service.price_usd}</p>
        </div>
      ))}
    </div>
  )
}

export const getServerSideProps: GetServerSideProps = async () => {
  const response = await fetch('https://get-dot-esim.replit.app/mcp/api')
  const data = await response.json()
  
  const services = Object.values(data.services)
    .flatMap((category: any) => category.services)
    .filter((service: any) => service.availability === 'Available')
  
  return { props: { services } }
}
```
```

Thank you for helping make the DOTM Platform MCP documentation better! 🚀
