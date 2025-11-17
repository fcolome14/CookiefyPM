#!/bin/bash

echo "🚀 Cookiefy Package Management - Setup"
echo "========================================"
echo ""

# Create directory structure
PACKAGES_DIR="$HOME/cookiefy-packages"
echo "📁 Setting up directory structure..."

mkdir -p "$PACKAGES_DIR/packages"
cd "$PACKAGES_DIR"

echo "✅ Created: $PACKAGES_DIR/packages/"
echo ""

# Make all scripts executable
echo "🔧 Making scripts executable..."
chmod +x *.sh 2>/dev/null
echo "✅ Scripts are now executable"
echo ""

# Check dependencies
echo "🔍 Checking dependencies..."
echo ""

MISSING_DEPS=()

# Check gcloud
if command -v gcloud &> /dev/null; then
    echo "   ✅ gcloud CLI installed"
    GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$GCLOUD_PROJECT" ]; then
        echo "      Current project: $GCLOUD_PROJECT"
    else
        echo "      ⚠️  No project set"
    fi
else
    echo "   ❌ gcloud CLI not found"
    MISSING_DEPS+=("gcloud")
fi

# Check gsutil
if command -v gsutil &> /dev/null; then
    echo "   ✅ gsutil installed"
else
    echo "   ❌ gsutil not found"
    MISSING_DEPS+=("gsutil")
fi

# Check optional dependencies
if command -v gh &> /dev/null; then
    echo "   ✅ GitHub CLI (gh) installed"
else
    echo "   ⚪ GitHub CLI (gh) not found (optional)"
fi

if command -v yq &> /dev/null; then
    echo "   ✅ yq installed"
else
    echo "   ⚪ yq not found (optional)"
fi

if command -v tree &> /dev/null; then
    echo "   ✅ tree installed"
else
    echo "   ⚪ tree not found (optional)"
fi

echo ""

# Show installation instructions if dependencies missing
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "❌ Missing required dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "📥 Installation instructions:"
    echo ""
    
    if [[ " ${MISSING_DEPS[*]} " =~ " gcloud " ]] || [[ " ${MISSING_DEPS[*]} " =~ " gsutil " ]]; then
        echo "   Google Cloud SDK (includes gcloud and gsutil):"
        echo "   macOS:   brew install google-cloud-sdk"
        echo "   Linux:   curl https://sdk.cloud.google.com | bash"
        echo ""
    fi
    
    echo "   Optional tools:"
    echo "   brew install gh yq tree"
    echo ""
    exit 1
fi

# Authentication check
echo "🔐 Checking authentication..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q @; then
    echo "   ✅ Authenticated with Google Cloud"
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo "      Account: $ACTIVE_ACCOUNT"
else
    echo "   ⚠️  Not authenticated with Google Cloud"
    echo ""
    read -p "Do you want to authenticate now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud auth login
    fi
fi

echo ""

# Project configuration
echo "⚙️  Project Configuration"
if [ -z "$GCLOUD_PROJECT" ]; then
    echo "   No project set. Please set your project:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
else
    echo "   ✅ Project: $GCLOUD_PROJECT"
    
    # Test bucket access
    echo ""
    echo "🪣 Testing bucket access..."
    if gsutil ls gs://cookiefy-media/temp-packages/ &> /dev/null; then
        echo "   ✅ Can access gs://cookiefy-media/temp-packages/"
    else
        echo "   ⚠️  Cannot access gs://cookiefy-media/temp-packages/"
        echo "      Make sure you have Storage Object Creator permissions"
    fi
fi

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "Directory structure:"
echo "$PACKAGES_DIR/"
echo "├── packages/           (your package data)"
echo "├── setup.sh"
echo "├── create-package.sh"
echo "├── validate-package.sh"
echo "├── upload-package.sh"
echo "└── upload-multiple.sh"
echo ""
echo "📋 Next Steps:"
echo "1. Create your first package:"
echo "   ./create-package.sh 2025-11-15-my-restaurant 2"
echo ""
echo "2. Edit the package files:"
echo "   - packages/2025-11-15-my-restaurant/sites.yaml"
echo "   - Add images to media/s01/bg/ and gallery/"
echo ""
echo "3. Validate your package:"
echo "   ./validate-package.sh 2025-11-15-my-restaurant"
echo ""
echo "4. Upload to production:"
echo "   ./upload-package.sh 2025-11-15-my-restaurant"
echo ""
echo "📖 Read README.md for detailed instructions"
echo ""