#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./create-package.sh <package_name> [num_sites]"
    echo "Example: ./create-package.sh 2025-11-15-barcelona 3"
    echo ""
    echo "This will create a package with the proper structure:"
    echo "  - manifest.yaml"
    echo "  - sites.yaml"
    echo "  - media/s01/bg/"
    echo "  - media/s01/gallery/"
    echo "  - media/s02/bg/  (if num_sites > 1)"
    echo "  - etc."
    exit 1
fi

PACKAGE_NAME=$1
NUM_SITES=${2:-1}
LOCAL_PACKAGES_DIR="$HOME/cookiefy-packages/packages"
PACKAGE_PATH="$LOCAL_PACKAGES_DIR/$PACKAGE_NAME"

if [ -d "$PACKAGE_PATH" ]; then
    echo "❌ Package already exists: $PACKAGE_NAME"
    exit 1
fi

echo "📦 Creating package: $PACKAGE_NAME"
echo "   Sites: $NUM_SITES"
echo ""

# Create main package directory
mkdir -p "$PACKAGE_PATH"

# Create media structure for each site
for i in $(seq -f "%02g" 1 $NUM_SITES); do
    mkdir -p "$PACKAGE_PATH/media/s$i/bg"
    mkdir -p "$PACKAGE_PATH/media/s$i/gallery"
    echo "   ✓ Created media/s$i/bg/"
    echo "   ✓ Created media/s$i/gallery/"
done

# Create manifest.yaml
cat > "$PACKAGE_PATH/manifest.yaml" << EOF
name: "$PACKAGE_NAME"
version: "1.0"
created: "$(date +%Y-%m-%d)"
description: "Restaurant data package for Cookiefy"
batch_id: "$PACKAGE_NAME"
source: "google"

# Package location context
location:
  name: "Barcelona"
  region: "Catalonia"
  country: "ES"
  lat: 41.3851
  lon: 2.1734
  zip_code: "08001"
EOF

echo "   ✓ Created manifest.yaml"

# Create sites.yaml template
cat > "$PACKAGE_PATH/sites.yaml" << 'EOF'
sites:
  - name: "Restaurant Name 1"
    street: "Carrer Example, 123"
    city: "Barcelona"
    province: "Barcelona"
    country: "ES"
    lat: 41.3851
    lon: 2.1734
    
    # Scoring
    score: 8.5
    num_opinions: 150
    
    # Details
    cuisine_type: "Mediterranean"
    price_range: "$$"
    description: "Amazing restaurant description here"
    contact: "+34 123 456 789"
    website: "https://restaurant1.com"
    
    # Opening hours
    opening_schedule:
      monday: "12:00-16:00, 20:00-23:00"
      tuesday: "12:00-16:00, 20:00-23:00"
      wednesday: "12:00-16:00, 20:00-23:00"
      thursday: "12:00-16:00, 20:00-23:00"
      friday: "12:00-16:00, 20:00-23:30"
      saturday: "12:00-16:00, 20:00-23:30"
      sunday: "12:00-16:00"
    
    # Special features
    is_halal: false
    is_gluten_free: false
    is_vegan: false
    
    # Media folder reference
    media_folder: "s01"
    
    # Hashtags for automatic list matching
    hashtags:
      - "mediterranean"
      - "seafood"
      - {"slug": "romantic", "weight": 2.5}
EOF

# Add additional sites if requested
if [ $NUM_SITES -gt 1 ]; then
    for i in $(seq 2 $NUM_SITES); do
        SITE_ID=$(printf "s%02d" $i)
        cat >> "$PACKAGE_PATH/sites.yaml" << EOF

  - name: "Restaurant Name $i"
    street: "Carrer Example, $((100 + i))"
    city: "Barcelona"
    province: "Barcelona"
    country: "ES"
    lat: 41.3851
    lon: 2.1734
    score: 8.5
    num_opinions: 150
    cuisine_type: "Mediterranean"
    price_range: "\$\$"
    description: "Amazing restaurant description here"
    contact: "+34 123 456 789"
    website: "https://restaurant$i.com"
    opening_schedule:
      monday: "12:00-16:00, 20:00-23:00"
      tuesday: "12:00-16:00, 20:00-23:00"
      wednesday: "12:00-16:00, 20:00-23:00"
      thursday: "12:00-16:00, 20:00-23:00"
      friday: "12:00-16:00, 20:00-23:30"
      saturday: "12:00-16:00, 20:00-23:30"
      sunday: "12:00-16:00"
    is_halal: false
    is_gluten_free: false
    is_vegan: false
    media_folder: "$SITE_ID"
    hashtags:
      - "mediterranean"
      - "seafood"
EOF
    done
fi

echo "   ✓ Created sites.yaml with $NUM_SITES site(s)"
echo ""

echo "✅ Package structure created successfully!"
echo ""
echo "📁 Location: $PACKAGE_PATH"
echo ""
echo "📋 Next steps:"
echo "1. Edit manifest.yaml - Update location info if needed"
echo "2. Edit sites.yaml - Add actual restaurant data"
echo "3. Add images:"
echo "   - Background: media/s01/bg/image.jpg"
echo "   - Gallery: media/s01/gallery/img1.jpg, img2.jpg, ..."
echo "4. Validate: ./validate-package.sh $PACKAGE_NAME"
echo "5. Upload: ./upload-package.sh $PACKAGE_NAME"
echo ""