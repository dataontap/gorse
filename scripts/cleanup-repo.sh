#!/bin/bash
set -e

echo "🧹 DOTM Repository Cleanup Script"
echo "=================================="
echo ""

REMOVED_COUNT=0
SPACE_FREED=0

# Function to remove files and count them
remove_files() {
    local pattern=$1
    local description=$2
    
    if [ -d "attached_assets" ]; then
        local count=$(find attached_assets -name "$pattern" 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            echo "🗑️  Removing $count $description..."
            find attached_assets -name "$pattern" -type f -delete 2>/dev/null || true
            REMOVED_COUNT=$((REMOVED_COUNT + count))
        fi
    fi
}

# Remove screenshot files
echo "📸 Removing screenshots and images..."
remove_files "Screenshot*.png" "screenshots"
remove_files "Screenshot*.jpg" "screenshot JPGs"
remove_files "image_*.png" "temporary images"
remove_files "PXL_*.jpg" "photo files"
remove_files "*.jpg" "remaining JPG files"

# Remove temporary and log files
echo "🧹 Removing temporary files..."
find . -type f \( -name "*.tmp" -o -name "*~" -o -name "*.bak" \) -not -path "./.git/*" -delete 2>/dev/null || true

# Remove empty directories (safely, excluding system paths)
echo "📁 Removing empty directories..."
find . -type d -empty \
    -not -path "./.git/*" \
    -not -path "./.cache/*" \
    -not -path "./.config/*" \
    -not -path "./node_modules/*" \
    -delete 2>/dev/null || true

# Remove attached_assets if empty
if [ -d "attached_assets" ] && [ -z "$(ls -A attached_assets 2>/dev/null)" ]; then
    echo "🗑️  Removing empty attached_assets directory..."
    rmdir attached_assets 2>/dev/null || true
fi

echo ""
echo "✅ Cleanup complete!"
echo "📊 Removed $REMOVED_COUNT files"
echo ""
echo "🎯 Files removed:"
echo "   - Screenshots and images from attached_assets/"
echo "   - Temporary files (*.tmp, *~, *.bak)"
echo "   - Empty directories"
echo ""
echo "💡 These file types are now in .gitignore to prevent future commits"
