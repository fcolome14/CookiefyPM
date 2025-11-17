#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: ./upload-package.sh <package_name>"
    echo "Example: ./upload-package.sh 2025-10-29-puigcerda"
    exit 1
fi

PACKAGE_NAME=$1
LOCAL_PACKAGES_DIR="$HOME/Documents/PROJECTS/cookiefy-packages/packages"
BUCKET="gs://cookiefy-media/temp-packages"

# Validate package structure
if [ ! -d "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME" ]; then
    echo "❌ Package directory not found: $LOCAL_PACKAGES_DIR/$PACKAGE_NAME"
    exit 1
fi

if [ ! -f "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/manifest.yaml" ]; then
    echo "❌ manifest.yaml not found in package"
    exit 1
fi

if [ ! -f "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/sites.yaml" ]; then
    echo "❌ sites.yaml not found in package"
    exit 1
fi

echo "📦 Packaging $PACKAGE_NAME..."
echo "   ✓ Found manifest.yaml"
echo "   ✓ Found sites.yaml"

# Check media structure
if [ -d "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/media" ]; then
    SITE_DIRS=$(find "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/media" -maxdepth 1 -type d -name 's*' | wc -l)
    TOTAL_IMAGES=0
    
    echo "   ✓ Found media/ with $SITE_DIRS site(s)"
    
    # Count images
    for SITE_DIR in "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/media"/s*/; do
        if [ -d "$SITE_DIR" ]; then
            SITE_NAME=$(basename "$SITE_DIR")
            BG_COUNT=0
            GALLERY_COUNT=0
            
            if [ -d "$SITE_DIR/bg" ]; then
                BG_COUNT=$(find "$SITE_DIR/bg" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) | wc -l)
            fi
            
            if [ -d "$SITE_DIR/gallery" ]; then
                GALLERY_COUNT=$(find "$SITE_DIR/gallery" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) | wc -l)
            fi
            
            TOTAL_IMAGES=$((TOTAL_IMAGES + BG_COUNT + GALLERY_COUNT))
            echo "     - $SITE_NAME: $BG_COUNT bg, $GALLERY_COUNT gallery"
        fi
    done
    
    echo "   ✓ Total images: $TOTAL_IMAGES"
else
    echo "   ⚠️  No media/ folder found"
fi

# Create tarball
echo ""
echo "🗜️  Creating archive..."
cd "$LOCAL_PACKAGES_DIR"
tar -czf "/tmp/$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME/"

# Get file size
SIZE=$(du -h "/tmp/$PACKAGE_NAME.tar.gz" | cut -f1)
echo "   ✓ Package size: $SIZE"

echo ""
echo "☁️  Uploading to Google Cloud Storage..."
gsutil -m cp "/tmp/$PACKAGE_NAME.tar.gz" "$BUCKET/"

echo ""
echo "✅ Package uploaded successfully!"
echo "   Location: $BUCKET/$PACKAGE_NAME.tar.gz"

# Cleanup temp file
rm "/tmp/$PACKAGE_NAME.tar.gz"

echo ""
# Optional: Auto-trigger the workflow
read -p "Do you want to trigger the import workflow now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v gh &> /dev/null; then
        gh workflow run import-package.yaml -f package_name="$PACKAGE_NAME"
        echo "🚀 Workflow triggered!"
        echo "   Check: https://github.com/YOUR_USERNAME/cookiefy/actions"
    else
        echo "⚠️  GitHub CLI not installed. Trigger manually:"
        echo "   Go to Actions (Project Cookiefy) → Import Data Package → Run workflow"
        echo "   Package name: $PACKAGE_NAME"
    fi
fi