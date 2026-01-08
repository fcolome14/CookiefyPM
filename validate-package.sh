#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./validate-package.sh <package_name>"
    echo "Example: ./validate-package.sh 2025-10-29-puigcerda"
    exit 1
fi

PACKAGE_NAME=$1
LOCAL_PACKAGES_DIR="$HOME/Documents/PROJECTS/CookiefyPM/packages"
PACKAGE_PATH="$LOCAL_PACKAGES_DIR/$PACKAGE_NAME"

echo "🔍 Validating package: $PACKAGE_NAME"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Check directory exists
if [ ! -d "$PACKAGE_PATH" ]; then
    echo "❌ Package directory not found: $PACKAGE_PATH"
    exit 1
fi

# Check manifest.yaml
echo "📄 Checking manifest.yaml..."
if [ -f "$PACKAGE_PATH/manifest.yaml" ]; then
    echo "   ✅ Found"
    if command -v yq &> /dev/null; then
        echo ""
        yq eval '.' "$PACKAGE_PATH/manifest.yaml" | sed 's/^/   /'
    fi
else
    echo "   ❌ Missing manifest.yaml"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check sites.yaml
echo "📄 Checking sites.yaml..."
if [ -f "$PACKAGE_PATH/sites.yaml" ]; then
    echo "   ✅ Found"
    if command -v yq &> /dev/null; then
        SITE_COUNT=$(yq eval '.sites | length' "$PACKAGE_PATH/sites.yaml")
        echo "   ℹ️  Sites defined: $SITE_COUNT"
        echo "   Sites:"
        yq eval '.sites[].name' "$PACKAGE_PATH/sites.yaml" | sed 's/^/     - /'
    fi
else
    echo "   ❌ Missing sites.yaml"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check media structure
echo "📁 Checking media structure..."
if [ -d "$PACKAGE_PATH/media" ]; then
    echo "   ✅ media/ folder found"
    
    # Find all site folders
    SITE_FOLDERS=$(find "$PACKAGE_PATH/media" -maxdepth 1 -type d -name 's*' | sort)
    SITE_COUNT=$(echo "$SITE_FOLDERS" | grep -c "s" || echo 0)
    
    if [ $SITE_COUNT -eq 0 ]; then
        echo "   ⚠️  No site folders (s01, s02, etc.) found"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "   ℹ️  Found $SITE_COUNT site folder(s)"
        echo ""
        
        # Check each site folder
        for SITE_DIR in $SITE_FOLDERS; do
            SITE_NAME=$(basename "$SITE_DIR")
            echo "   📂 $SITE_NAME/"
            
            # Check bg folder
            if [ -d "$SITE_DIR/bg" ]; then
                BG_COUNT=$(find "$SITE_DIR/bg" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) | wc -l)
                if [ $BG_COUNT -eq 0 ]; then
                    echo "      ⚠️  bg/ folder is empty"
                    WARNINGS=$((WARNINGS + 1))
                else
                    echo "      ✅ bg/ - $BG_COUNT image(s)"
                fi
            else
                echo "      ⚠️  bg/ folder missing"
                WARNINGS=$((WARNINGS + 1))
            fi
            
            # Check gallery folder
            if [ -d "$SITE_DIR/gallery" ]; then
                GALLERY_COUNT=$(find "$SITE_DIR/gallery" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) | wc -l)
                if [ $GALLERY_COUNT -eq 0 ]; then
                    echo "      ⚠️  gallery/ folder is empty"
                    WARNINGS=$((WARNINGS + 1))
                else
                    echo "      ✅ gallery/ - $GALLERY_COUNT image(s)"
                fi
            else
                echo "      ⚠️  gallery/ folder missing"
                WARNINGS=$((WARNINGS + 1))
            fi
            
            echo ""
        done
    fi
else
    echo "   ⚠️  media/ folder not found"
    WARNINGS=$((WARNINGS + 1))
fi

echo "=========================================="
echo "VALIDATION RESULTS"
echo "=========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ Package is valid and ready to upload!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Package has $WARNINGS warning(s) but can be uploaded"
    exit 0
else
    echo "❌ Package has $ERRORS error(s) and $WARNINGS warning(s)"
    echo "   Fix errors before uploading"
    exit 1
fi