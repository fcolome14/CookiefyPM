#!/bin/bash

set -e

LOCAL_PACKAGES_DIR="$HOME/Documents/PROJECTS/CookiefyPM/packages"
BUCKET="gs://cookiefy-media/temp-packages"

if [ $# -eq 0 ]; then
    echo "Usage: ./upload-multiple.sh <package1> <package2> ..."
    echo "Example: ./upload-multiple.sh 2025-10-29-puigcerda 2025-10-30-el-masnou"
    echo ""
    echo "Or use 'all' to upload all packages:"
    echo "./upload-multiple.sh all"
    exit 1
fi

# If 'all' is specified, get all package directories
if [ "$1" = "all" ]; then
    PACKAGES=($(ls -1 "$LOCAL_PACKAGES_DIR"))
else
    PACKAGES=("$@")
fi

UPLOADED=()
FAILED=()
TOTAL_SIZE=0

echo "========================================"
echo "Batch Package Upload"
echo "========================================"
echo "Packages to process: ${#PACKAGES[@]}"
echo ""

for PACKAGE_NAME in "${PACKAGES[@]}"; do
    echo "=========================================="
    echo "Processing: $PACKAGE_NAME"
    echo "=========================================="
    
    if [ ! -d "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME" ]; then
        echo "❌ Package not found, skipping..."
        FAILED+=("$PACKAGE_NAME (not found)")
        continue
    fi
    
    if [ ! -f "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/manifest.yaml" ] || \
       [ ! -f "$LOCAL_PACKAGES_DIR/$PACKAGE_NAME/sites.yaml" ]; then
        echo "❌ Missing required files, skipping..."
        FAILED+=("$PACKAGE_NAME (incomplete)")
        continue
    fi
    
    cd "$LOCAL_PACKAGES_DIR"
    tar -czf "/tmp/$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME/"
    
    SIZE_BYTES=$(stat -f%z "/tmp/$PACKAGE_NAME.tar.gz" 2>/dev/null || stat -c%s "/tmp/$PACKAGE_NAME.tar.gz")
    TOTAL_SIZE=$((TOTAL_SIZE + SIZE_BYTES))
    
    if gsutil -m cp "/tmp/$PACKAGE_NAME.tar.gz" "$BUCKET/"; then
        echo "✅ $PACKAGE_NAME uploaded"
        UPLOADED+=("$PACKAGE_NAME")
        rm "/tmp/$PACKAGE_NAME.tar.gz"
    else
        echo "❌ Upload failed for $PACKAGE_NAME"
        FAILED+=("$PACKAGE_NAME (upload failed)")
        rm -f "/tmp/$PACKAGE_NAME.tar.gz"
    fi
    
    echo ""
done

# Convert total size to human readable
TOTAL_SIZE_MB=$((TOTAL_SIZE / 1024 / 1024))

echo "=========================================="
echo "UPLOAD SUMMARY"
echo "=========================================="
echo "✅ Successfully uploaded: ${#UPLOADED[@]} packages"
echo "   Total size: ${TOTAL_SIZE_MB}MB"
for pkg in "${UPLOADED[@]}"; do
    echo "   ✓ $pkg"
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed: ${#FAILED[@]} packages"
    for pkg in "${FAILED[@]}"; do
        echo "   ✗ $pkg"
    done
fi

if [ ${#UPLOADED[@]} -gt 0 ]; then
    echo ""
    read -p "Trigger import workflows for uploaded packages? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v gh &> /dev/null; then
            for pkg in "${UPLOADED[@]}"; do
                echo "🚀 Triggering workflow for $pkg..."
                gh workflow run import-package.yaml -f package_name="$pkg"
                sleep 2  # Avoid rate limiting
            done
            echo "✅ All workflows triggered!"
        else
            echo "⚠️  GitHub CLI not installed"
            echo "Manually trigger workflows for these packages:"
            for pkg in "${UPLOADED[@]}"; do
                echo "   - $pkg"
            done
        fi
    fi
fi