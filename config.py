# config.py
"""Configuration for the scraper"""

# Locations to scrape (one YAML file per location)
LOCATIONS = {
    # Small towns (no neighborhood)
    "towns": [
        {"name": "Badalona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Montgat", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Tiana", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
    ],
    
    # Barcelona neighborhoods (include neighborhood name)
    "barcelona_neighborhoods": [
        {"name": "Gràcia", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Eixample", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Ciutat Vella", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Les Corts", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Sarrià-Sant Gervasi", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Horta-Guinardó", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Nou Barris", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Sant Andreu", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
        {"name": "Sant Martí", "city": "Barcelona", "province": "Barcelona", "region": "Catalunya", "country": "ES"},
    ]
}

# Scraper settings
SCRAPER_CONFIG = {
    "headless": False,
    "scroll_pause": 2.0,  # Increased for better loading - was 2.0
    "max_scrolls": 350,  # Increased from 200
    "page_load_delay": 1500,
    "between_restaurants_delay": 800,
    "between_locations_delay": 3000,
}

# Output settings
OUTPUT_DIR = "output"