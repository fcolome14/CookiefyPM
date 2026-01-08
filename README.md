# Cookiefy Package Management System

Local management system for Cookiefy sites data packages. Keep your package data **outside** your Git repository to avoid bloating your Docker containers.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Workflow Overview](#workflow-overview)
- [Detailed Usage](#detailed-usage)
- [Package Structure](#package-structure)
- [Scraper](#scraper)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## 🚀 Quick Start

```bash
# 1. First time setup
./setup.sh

# 2. Create a new package following the expected format: YYYY-MM-DD-city
./create-package.sh 2025-11-15-barcelona

# 3. Edit sites.yaml and add images
# Edit: packages/2025-11-15-barcelona/sites.yaml
# Add images to: packages/2025-11-15-barcelona/media/s01/bg/ and gallery/

# 4. Validate your package
./validate-package.sh 2025-11-15-barcelona

# 5. Upload to cloud and trigger import
./upload-package.sh 2025-11-15-barcelona
```

---

## 📦 Prerequisites

### Required
- **gcloud CLI** - Google Cloud SDK
- **gsutil** - Google Cloud Storage tool (comes with gcloud)
- **Python 3** - For YAML validation (optional but recommended)

### Optional
- **GitHub CLI (gh)** - For automatic workflow triggering
- **yq** - For better YAML validation
- **tree** - For visualizing directory structure

### Install Prerequisites

**macOS:**
```bash
# Install gcloud
brew install google-cloud-sdk

# Install optional tools
brew install gh yq tree
```

**Linux:**
```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install optional tools
sudo apt install jq tree
brew install gh yq  # or download from GitHub
```

**Windows:**

Using `Git Bash`:

1. Install it from `Powershell`:

    ```powershell
    winget install Git.Git
    ```

2. Open `Git Bash` and run:

    ```bash
    mkdir -p ~/CookiefyPM/packages # (if not created yet)
    cd ~/CookiefyPM

    # Download all the .sh scripts here
    chmod +x *.sh
    ./setup.sh
    ```
3. Use normally:

    ```bash
    ./create-package.sh 2025-11-15-barcelona
    ./validate-package.sh 2025-11-15-barcelona
    ./upload-package.sh 2025-11-15-barcelona
    ```

---

## 🛠️ Installation

### Step 1: Create Directory Structure

```bash
mkdir -p ~/CookiefyPM/packages
cd ~/CookiefyPM
```

### Step 2: Download Scripts

Save all the scripts from this repository:
- `setup.sh`
- `create-package.sh`
- `validate-package.sh`
- `upload-package.sh`
- `upload-multiple.sh`

### Step 3: Make Scripts Executable

```bash
chmod +x *.sh
```

### Step 4: Run Setup

> **IMPORTANT**: Make sure the temporal folder exists in the `Google Cloud` bucket for your target project. Open Google Console on your project and do this if `temp-packages` does not exist:

  ```bash
    # Create the temp-packages folder by uploading a placeholder file
    echo "This folder is for temporary package uploads" > README.txt
    gsutil cp README.txt gs://cookiefy-media/temp-packages/README.txt
    rm README.txt

    # Verify it was created
    gsutil ls gs://cookiefy-media/temp-packages/
    # Expected output:**
    gs://cookiefy-media/temp-packages/README.txt
  ``` 

Once verified `temp-packages` exists in the bucket, run on Git Bash:

```bash
./setup.sh
```

This will:
- Check for required dependencies
- Guide you through gcloud authentication
- Set up your project configuration

### Step 5: Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify access to the bucket
gsutil ls gs://cookiefy-media/temp-packages/
```

### Step 6: (Optional) Authenticate with GitHub

```bash
gh auth login
```

This enables automatic workflow triggering.

---

## 🔄 Workflow Overview

```
┌──────────────────────────────────────────────────────────┐
│ 1. CREATE PACKAGE LOCALLY (YOUR PC)                      │
│    ~/CookiefyPM/packages/2025-11-15-barcelona/    │
│    ├── manifest.yaml                                     │
│    ├── sites.yaml                                        │
│    └── media/s01/bg/ & gallery/                          │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 2. VALIDATE PACKAGE                                       │
│    ./validate-package.sh 2025-11-15-barcelona            │
│    ✓ Checks manifest.yaml                                │
│    ✓ Checks sites.yaml                                   │
│    ✓ Verifies media structure                            │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 3. UPLOAD TO GOOGLE CLOUD STORAGE                         │
│    ./upload-package.sh 2025-11-15-barcelona              │
│    → gs://cookiefy-media/temp-packages/*.tar.gz          │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 4. TRIGGER GITHUB ACTIONS                                 │
│    Workflow: import-package.yaml                         │
│    Input: package_name = 2025-11-15-barcelona            │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 5. CLOUD RUN JOB IMPORTS TO PRODUCTION                    │
│    ✓ Downloads package from GCS                          │
│    ✓ Imports data to PostgreSQL                          │
│    ✓ Uploads images to gs://cookiefy-media/media/        │
│    ✓ Cleans up temp files                                │
└──────────────────────────────────────────────────────────┘
```

---

## 📖 Detailed Usage

### Creating a New Package

```bash
# Create package with 3 restaurant sites
./create-package.sh 2025-11-15-barcelona

# This creates:
# packages/2025-11-15-barcelona/
# ├── manifest.yaml
# ├── sites.yaml
# └── media/
#     ├── s01/bg/ & gallery/
#     ├── s02/bg/ & gallery/
#     └── s03/bg/ & gallery/
```

### Editing Package Data

#### 1. Edit manifest.yaml

```yaml
name: "2025-11-15-barcelona"
version: "1.0"
created: "2025-11-15"
description: "Restaurant data package for Barcelona"
batch_id: "2025-11-15-barcelona"
source: "google"

# Location metadata (for the package location table)
location:
  name: "Barcelona"
  region: "Catalonia"
  country: "ES"
  lat: 41.3851
  lon: 2.1734
  zip_code: "08001"
```

#### 2. Edit sites.yaml

```yaml
sites:
  - name: "Restaurant Name"
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
    price_range: "10-20€" # Always same format (x-y€) and ranges: 1-10€, 10-20€, 30-50€, >70€, >100€
    description: "Amazing restaurant description" # must be an extended description (otherwise keep it empty "")
    contact: "+34 123 456 789" # If available
    website: "https://restaurant.com" # If available
    
    # Opening hours. Important to follow this exact format
    opening_schedule: 
      timezone: "Europe/Madrid"
      weekly:
        mon:
          - { closed: true }
        tue:
          - { start: "10:00", end: "17:30" }
        wed:
          - { start: "10:00", end: "17:30" }
        thu:
          - { start: "10:00", end: "17:30" }
        fri:
          - { start: "10:00", end: "17:30" }
        sat:
          - { start: "10:00", end: "17:30" }
        sun:
          - { start: "10:00", end: "17:30" }
      exceptions:
        - { date: "2025-12-25", closed: true }
    
    # Special features
    is_halal: false
    is_gluten_free: true
    is_vegan: false
    
    # Media folder reference (matches folder name in media/)
    media_folder: "s01"
    
    # Hashtags for automatic list matching
    # Weight for each tag: 0-5
    hashtags:
      - "mediterranean"
      - "seafood"
      - {"slug": "romantic", "weight": 2.5}
      - {"slug": "family-friendly", "weight": 1.5}
    
    # Awards. If no awards keep it empty --> awards: {}
    awards:
    - award_slug: "michelin-one-star" # must match Awards.slug
      description: "Michelin 1 Star"
      year: 2024
      reference: "https://guide.michelin.com/en/catalunya/el-masnou/restaurant/tresmacarrons" # any reference string
    
    # Social Media. If no social media keep it empty --> social_media: {}
    social_media:
    - source: tiktok
      link: "https://www.tiktok.com/@notodofoodies/video/7194833102831701254?is_from_webapp=1&sender_device=pc&web_id=7551495304508425750"
    - source: tiktok
      link: "https://www.tiktok.com/@bcngourmet/video/7035708647132892421?is_from_webapp=1&sender_device=pc&web_id=7551495304508425750"
    
```

#### 3. Add Images

```bash
# Add background image (main hero image)
cp restaurant-hero.jpg packages/2025-11-15-barcelona/media/s01/bg/

# Add gallery images
cp image1.jpg packages/2025-11-15-barcelona/media/s01/gallery/
cp image2.jpg packages/2025-11-15-barcelona/media/s01/gallery/
cp image3.jpg packages/2025-11-15-barcelona/media/s01/gallery/
```

**Supported formats:** `.jpg`, `.jpeg`, `.png`, `.webp`

### Validating Your Package

> **NOTE**: Adjust your `LOCAL_PACKAGES_DIR` path where you are keeping your packages 

```bash
# Validate before uploading
./validate-package.sh 2025-11-15-barcelona
```

**Output example:**
```
🔍 Validating package: 2025-11-15-barcelona
==========================================

📄 Checking manifest.yaml...
   ✅ Found
   
   name: 2025-11-15-barcelona
   version: 1.0
   created: 2025-11-15

📄 Checking sites.yaml...
   ✅ Found
   ℹ️  Sites defined: 3
   Sites:
     - Restaurant Name 1
     - Restaurant Name 2
     - Restaurant Name 3

📁 Checking media structure...
   ✅ media/ folder found
   ℹ️  Found 3 site folder(s)
   
   📂 s01/
      ✅ bg/ - 1 image(s)
      ✅ gallery/ - 5 image(s)
   
   📂 s02/
      ✅ bg/ - 1 image(s)
      ✅ gallery/ - 3 image(s)

==========================================
VALIDATION RESULTS
==========================================
✅ Package is valid and ready to upload!
```

### Uploading Packages

> **NOTE**: Adjust your `LOCAL_PACKAGES_DIR` path where you are keeping your packages 

#### Single Package Upload

```bash
./upload-package.sh 2025-11-15-barcelona

# Output:
# 📦 Packaging 2025-11-15-barcelona...
#    ✓ Found manifest.yaml
#    ✓ Found sites.yaml
#    ✓ Found media/ with 3 site(s)
#      - s01: 1 bg, 5 gallery
#      - s02: 1 bg, 3 gallery
#      - s03: 1 bg, 4 gallery
#    ✓ Total images: 24
# 
# 🗜️  Creating archive...
#    ✓ Package size: 15M
# 
# ☁️  Uploading to Google Cloud Storage...
# 
# ✅ Package uploaded successfully!
#    Location: gs://cookiefy-media/temp-packages/2025-11-15-barcelona.tar.gz
# 
# Do you want to trigger the import workflow now? (y/n)
```

#### Batch Upload

```bash
# Upload multiple packages
./upload-multiple.sh package1 package2 package3

# Upload all packages
./upload-multiple.sh all
```

**Output example:**
```
==========================================
Batch Package Upload
==========================================
Packages to process: 3

==========================================
Processing: 2025-11-15-barcelona
==========================================
✅ 2025-11-15-barcelona uploaded

==========================================
Processing: 2025-11-16-girona
==========================================
✅ 2025-11-16-girona uploaded

==========================================
UPLOAD SUMMARY
==========================================
✅ Successfully uploaded: 2 packages
   Total size: 28MB
   ✓ 2025-11-15-barcelona
   ✓ 2025-11-16-girona

Trigger import workflows for uploaded packages? (y/n)
```

### Triggering Import to Production

After uploading, you have two options:

#### Option 1: Automatic (via upload script)

The upload script will ask if you want to trigger the import. Type `y` to proceed.

#### Option 2: Manual (via GitHub)

1. Go to your repository on GitHub
2. Navigate to **Actions** tab
3. Select **Import Data Package** workflow
4. Click **Run workflow**
5. Enter the package name (e.g., `2025-11-15-barcelona`)
6. Click **Run workflow**

#### Option 3: Manual (via GitHub CLI)

```bash
gh workflow run import-package.yaml -f package_name="2025-11-15-barcelona"
```

### Monitoring Import Progress

```bash
# Watch GitHub Actions logs
gh run watch

# Or visit GitHub Actions UI
# https://github.com/YOUR_USERNAME/cookiefy/actions
```

---

## 📁 Package Structure Reference

### Complete Package Example

```
2025-11-15-barcelona/
├── manifest.yaml               # Package metadata
├── sites.yaml                  # Restaurant data
└── media/                      # Organized by site
    ├── s01/                    # Site 1 media
    │   ├── bg/
    │   │   └── IMG_001.jpg    # Background/hero image
    │   └── gallery/
    │       ├── IMG_002.jpg    # Gallery images
    │       ├── IMG_003.jpg
    │       └── IMG_004.jpg
    ├── s02/                   # Site 2 media
    │   ├── bg/
    │   │   └── IMG_005.jpg
    │   └── gallery/
    │       ├── IMG_006.jpg
    │       └── IMG_007.jpg
    └── s03/                   # Site 3 media
        ├── bg/
        │   └── IMG_008.jpg
        └── gallery/
            ├── IMG_009.jpg
            └── IMG_010.jpg
```

### Manifest.yaml Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ Yes | Package name (should match folder name) |
| `version` | ✅ Yes | Package version (e.g., "1.0") |
| `batch_id` | ✅ Yes | Unique identifier for this import batch |
| `created` | ✅ Yes | Creation date (YYYY-MM-DD) |
| `source` | ⚪ No | Data source (e.g., "manual", "google", "thefork") |
| `location` | ✅ Yes | Geographic context for the package |
| `location.name` | ✅ Yes | Location name (e.g., "Barcelona") |
| `location.region` | ⚪ No | Region/state (e.g., "Catalonia") |
| `location.country` | ✅ Yes | ISO country code (e.g., "ES") |
| `location.lat` | ✅ Yes | Latitude |
| `location.lon` | ✅ Yes | Longitude |
| `location.zip_code` | ⚪ No | Postal code |

### Sites.yaml Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ Yes | Restaurant name |
| `street` | ✅ No | Street address |
| `city` | ✅ No | City |
| `province` | ✅ No | Province/state |
| `country` | ✅ No | ISO country code |
| `lat` | ✅ No | Latitude (recommended for map features) |
| `lon` | ✅ No | Longitude (recommended for map features) |
| `score` | ⚪ No | Rating (0-10) |
| `num_opinions` | ⚪ No | Number of reviews |
| `cuisine_type` | ⚪ No | Type of cuisine |
| `price_range` | ⚪ No | Price indicator ($, $$, $$$, $$$$) |
| `description` | ⚪ No | Restaurant description |
| `contact` | ⚪ No | Phone number |
| `website` | ⚪ No | Website URL |
| `opening_schedule` | ⚪ No | Opening hours by day |
| `media_folder` | ✅ Yes* | Folder name in media/ (e.g., "s01") |
| `hashtags` | ✅ No | List of hashtags for categorization |
| `awards` | ⚪ No | List of awards/recognitions |
| `social_media` | ⚪ No | Social media links |

*Required if you have media for this site

---

## 🐶 Scraper

The scraping automatic process is led by `chroium` and `playwright` libraries. 

Install the dependencies:

```bash
poetry add playwright pyyaml
poetry run playwright install chromium
```

---

## 🔧 Troubleshooting

### Upload Issues

**Problem:** `gsutil: command not found`
```bash
# Solution: Install Google Cloud SDK
brew install google-cloud-sdk  # macOS
# or
curl https://sdk.cloud.google.com | bash  # Linux
```

**Problem:** `AccessDeniedException: 403`
```bash
# Solution: Re-authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**Problem:** Package upload timeout
```bash
# Solution: Check your internet connection and package size
# Large packages (>100MB) may take time
# Consider compressing images before adding to package
```

### Validation Issues

**Problem:** `❌ manifest.yaml missing`
```bash
# Solution: Ensure manifest.yaml exists
ls packages/YOUR_PACKAGE_NAME/manifest.yaml

# If missing, create it using the template above
```

**Problem:** `⚠️ bg/ folder is empty`
```bash
# Solution: Add at least one background image
cp your-image.jpg packages/YOUR_PACKAGE_NAME/media/s01/bg/
```

**Problem:** `⚠️ No site folders found`
```bash
# Solution: Ensure media folders are named s01, s02, etc.
# NOT site1, restaurant1, or other names
mv packages/YOUR_PACKAGE/media/site1 packages/YOUR_PACKAGE/media/s01
```

### Import Issues

**Problem:** GitHub Actions workflow fails
```bash
# Solution: Check the logs in GitHub Actions
# Common issues:
# 1. Package not found in GCS → Re-upload
# 2. Invalid YAML syntax → Validate locally
# 3. Database connection issue → Check Cloud Run logs
```

**Problem:** Images not appearing in app
```bash
# Solution: 
# 1. Verify images were uploaded to GCS
gsutil ls gs://cookiefy-media/media/sites/

# 2. Check image formats (must be jpg, jpeg, png, or webp)
# 3. Ensure media_folder in sites.yaml matches folder name
```

---

## ❓ FAQ

### Q: Can I edit a package after uploading?

**A:** Yes! Just edit the package locally, re-validate, and re-upload. The import script is idempotent (it updates existing data based on `batch_id`).

### Q: How do I delete a package?

**A:** Delete it locally:
```bash
rm -rf packages/YOUR_PACKAGE_NAME
```

To remove from production, you'll need to use database tools (not covered by these scripts).

### Q: Can I import to my local development database?

**A:** Yes! Use the main import script directly:
```bash
cd /path/to/cookiefy-project
python data/scripts/import_package.py \
  --dir ~/CookiefyPM/packages/YOUR_PACKAGE \
  --env development \
  --verbose
```

### Q: What happens if I upload the same package twice?

**A:** The package tarball will be replaced in GCS. If you trigger the import twice, the second import will detect it's already been applied and skip it (based on `batch_id`).

### Q: How much does GCS storage cost?

**A:** Very little! Example:
- 100 packages × 20MB average = 2GB
- GCS Standard Storage: ~$0.05/month
- Plus minimal egress costs

### Q: Can I share packages with team members?

**A:** Yes! Share the entire `~/CookiefyPM/` directory (or specific packages). They just need to:
1. Set up gcloud authentication
2. Run `./upload-package.sh PACKAGE_NAME`

### Q: Where can I see what packages have been imported?

**A:** Query your database:
```sql
SELECT batch_id, source, created_at, notes 
FROM ingestion_batches 
ORDER BY created_at DESC;
```

---

## 📞 Support

If you encounter issues:

1. **Check the logs** in GitHub Actions
2. **Verify your setup** with `./setup.sh`
3. **Test locally first** before importing to production
4. **Check permissions** for GCS bucket access

---

## 🎉 Success Checklist

- [ ] `gcloud` and `gsutil` installed and authenticated
- [ ] Scripts downloaded and made executable
- [ ] Can create packages with `./create-package.sh`
- [ ] Can validate packages with `./validate-package.sh`
- [ ] Can upload packages with `./upload-package.sh`
- [ ] Can trigger GitHub Actions workflow
- [ ] Can see imported data in production

**You're ready to manage Cookiefy packages! 🚀**
