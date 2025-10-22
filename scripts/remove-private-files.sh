#!/bin/bash
set -e

echo "🔒 Removing Private Files from Git Repository"
echo "=============================================="
echo ""

# Remove files from git tracking (but keep locally)
echo "📦 Removing from git tracking..."

# Remove attached_assets directory
if [ -d "attached_assets" ]; then
    git rm -r --cached attached_assets/ 2>/dev/null || true
    echo "✓ Removed attached_assets/"
fi

# Remove zip files
git rm --cached *.zip 2>/dev/null || true
echo "✓ Removed *.zip files"

# Remove SQL files
git rm --cached *.sql 2>/dev/null || true
echo "✓ Removed *.sql files"

# Remove PDF files  
git rm --cached *.pdf attached_assets/*.pdf 2>/dev/null || true
echo "✓ Removed *.pdf files"

# Remove debug/utility scripts
git rm --cached add_oxio_*.py 2>/dev/null || true
git rm --cached check_*.py 2>/dev/null || true
git rm --cached debug_*.py 2>/dev/null || true
git rm --cached analyze_*.py 2>/dev/null || true
git rm --cached create_batch_*.py 2>/dev/null || true
git rm --cached create_download_*.py 2>/dev/null || true
git rm --cached create_secure_*.py 2>/dev/null || true
git rm --cached create_basic_*.py 2>/dev/null || true
echo "✓ Removed debug/utility scripts"

# Remove example data
git rm --cached example_user_data.json 2>/dev/null || true
echo "✓ Removed example data"

# Remove internal documentation
git rm --cached GITHUB_UPLOAD_GUIDE.md 2>/dev/null || true
echo "✓ Removed GITHUB_UPLOAD_GUIDE.md"

# Remove gradle files
git rm --cached build.gradle.kts 2>/dev/null || true
echo "✓ Removed gradle files"

echo ""
echo "✅ Private files removed from git tracking!"
echo ""
echo "Note: Files are kept locally but won't be pushed to GitHub"
echo "Run: git commit -m 'Remove private files from repository' && git push origin main"
