#!/bin/bash

###############################################################################
# Automated GitHub Push Script for DOTM Platform
# Automatically stages, commits, and pushes changes to GitHub
###############################################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     DOTM Platform - Automated GitHub Push Script        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${RED}✗ Error: Not a git repository${NC}"
    echo "Run: git init"
    exit 1
fi

# Configure git remote if not set
REMOTE_URL="https://github.com/dataontap/gorse.git"
if ! git remote get-url origin &>/dev/null; then
    echo -e "${YELLOW}⚙  Configuring remote origin...${NC}"
    git remote add origin "$REMOTE_URL"
    echo -e "${GREEN}✓ Remote configured: $REMOTE_URL${NC}"
fi

# Configure git user if not set
if [ -z "$(git config user.name)" ]; then
    git config user.name "DOT"
    echo -e "${GREEN}✓ Git user configured${NC}"
fi

if [ -z "$(git config user.email)" ]; then
    git config user.email "aa@dotmobile.app"
    echo -e "${GREEN}✓ Git email configured${NC}"
fi

echo ""
echo -e "${BLUE}🧹 Running repository cleanup...${NC}"
echo ""

# Run cleanup script if it exists
if [ -f "scripts/cleanup-repo.sh" ]; then
    bash scripts/cleanup-repo.sh
    echo ""
else
    echo -e "${YELLOW}⚠  Cleanup script not found, skipping cleanup${NC}"
    echo ""
fi

echo -e "${BLUE}📊 Checking repository status...${NC}"
echo ""

# Show current branch
BRANCH=$(git branch --show-current)
echo -e "${GREEN}Branch: ${BRANCH}${NC}"

# Check for changes
if git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠  No changes to commit${NC}"
    echo ""
    echo -e "${BLUE}Repository is up to date with latest commit:${NC}"
    git log -1 --pretty=format:"%h - %s (%cr) <%an>" --abbrev-commit
    echo ""
    exit 0
fi

echo ""
echo -e "${BLUE}📝 Files to be committed:${NC}"
git status --short | head -20
echo ""

# Default commit message
DEFAULT_MSG="🚀 Auto-deploy updates from Replit"

# Use provided commit message or default
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    COMMIT_MSG="$DEFAULT_MSG"
fi

echo -e "${YELLOW}📦 Staging changes...${NC}"
git add .

echo -e "${YELLOW}💾 Committing changes...${NC}"
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}✓ Changes committed${NC}"
echo ""

echo -e "${YELLOW}🚀 Pushing to GitHub...${NC}"
git push -u origin "$BRANCH"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✓ Successfully pushed to GitHub!            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Repository: ${REMOTE_URL}${NC}"
echo -e "${BLUE}Branch: ${BRANCH}${NC}"
echo ""
echo -e "${GREEN}Latest commit:${NC}"
git log -1 --pretty=format:"%h - %s (%cr) <%an>" --abbrev-commit
echo ""
echo ""
