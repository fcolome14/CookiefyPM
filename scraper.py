# scraper.py
"""Google Maps restaurant scraper for Cookiefy"""

from playwright.sync_api import sync_playwright
import yaml
import re
import os
from datetime import datetime
from pathlib import Path
from config import LOCATIONS, SCRAPER_CONFIG, OUTPUT_DIR


class CookiefyRestaurantScraper:
    def __init__(self):
        self.config = SCRAPER_CONFIG
        
    def extract_coordinates_from_url(self, url):
        """Extract lat/lon from Google Maps URL - Enhanced with multiple patterns"""
        # Pattern 1: Standard format @lat,lon,zoom
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+),\d+', url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Pattern 2: Without zoom @lat,lon
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Pattern 3: In the place ID section !3d(lat)!4d(lon)
        match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        return None, None
    
    def create_restaurant_template(self, location_info):
        """Create restaurant object with Cookiefy format"""
        return {
            'source': 'google',
            'name': '',
            'score': None,  # Will be number, not string
            'num_opinions': None,  # Will be number, not string
            'street': '',
            'lat': None,  # Will be number, not string
            'lon': None,  # Will be number, not string
            'price': '',
            'dishes': '',
            'neighborhood': location_info.get('neighborhood', ''),
            'city': location_info.get('city', location_info.get('name', '')),
            'region': location_info.get('region', ''),
            'province': location_info.get('province', ''),
            'country': location_info.get('country', ''),
            'contact': '',
            'website': '',
            'media_folder': '',
            'image_slug': 'no-image',
            'category_slug': 'restaurant',
            'description': '',
            'opening_schedule': {
                'timezone': 'Europe/Madrid',
                'weekly': {
                    'mon': [{'closed': True}],
                    'tue': [{'closed': True}],
                    'wed': [{'closed': True}],
                    'thu': [{'closed': True}],
                    'fri': [{'closed': True}],
                    'sat': [{'closed': True}],
                    'sun': [{'closed': True}],
                },
                'exceptions': [{'date': '2025-12-25', 'closed': True}]
            },
            'menu': {},
            'is_halal': False,
            'is_gluten_free': False,
            'is_vegan': False,
            'active': True,
            'cuisine_type': '',
            'social_media': {},
            'hashtags': []
        }

    def handle_cookie_consent(self, page):
        """Handle Google Maps cookie consent dialog - improved version"""
        try:
            print("🍪 Waiting for cookie consent dialog...")
            
            # Wait longer for the dialog to appear
            page.wait_for_timeout(2000)
            
            # Strategy 1: Try by button text (most reliable)
            reject_texts = [
                "Reject all",
                "Rechazar todo", 
                "Rebutjar-ho tot",
                "Reject",
                "Rechazar",
                "Rebutjar"
            ]
            
            for text in reject_texts:
                try:
                    # Use get_by_role which is more reliable
                    button = page.get_by_role("button", name=re.compile(text, re.IGNORECASE))
                    if button.count() > 0:
                        button.first.click(timeout=2000)
                        print(f"✅ Clicked '{text}' button")
                        page.wait_for_timeout(1500)
                        return True
                except Exception as e:
                    continue
            
            # Strategy 2: Try by text content (case insensitive)
            for text in reject_texts:
                try:
                    button = page.locator(f"button:has-text('{text}')").first
                    if button.is_visible(timeout=1000):
                        button.click()
                        print(f"✅ Clicked button containing '{text}'")
                        page.wait_for_timeout(1500)
                        return True
                except:
                    continue
            
            # Strategy 3: Try common Google cookie dialog classes
            selectors = [
                'button:has-text("Reject")',
                'button:has-text("Rechazar")',
                'button:has-text("Rebutjar")',
                'button.tHlp8d',  # Common Google reject button class
                'form[action*="consent"] button:first-child',
                'div[jsname="V67aGc"] button',
            ]
            
            for selector in selectors:
                try:
                    buttons = page.locator(selector).all()
                    for button in buttons:
                        if button.is_visible(timeout=500):
                            button.click()
                            print(f"✅ Clicked button with selector: {selector}")
                            page.wait_for_timeout(1500)
                            return True
                except:
                    continue
            
            # Strategy 4: Check for iframe
            try:
                frames = page.frames
                for frame in frames:
                    if 'consent' in frame.url.lower() or 'cookie' in frame.url.lower():
                        print(f"  Found consent iframe: {frame.url}")
                        for text in reject_texts:
                            try:
                                button = frame.get_by_role("button", name=re.compile(text, re.IGNORECASE))
                                if button.count() > 0:
                                    button.first.click()
                                    print(f"✅ Clicked '{text}' in iframe")
                                    page.wait_for_timeout(1500)
                                    return True
                            except:
                                continue
            except:
                pass
            
            print("ℹ️  No cookie dialog found (may be already accepted)")
            return False
            
        except Exception as e:
            print(f"⚠️  Cookie handling error: {e}")
            print("   Continuing anyway...")
            return False
    

    def scrape_location(self, location_info):
        """Scrape all restaurants in a location"""
        location_name = location_info.get('name', '')
        city = location_info.get('city', location_name)
        is_barcelona_neighborhood = 'city' in location_info and location_info['city'] == 'Barcelona'
        
        print(f"\n{'='*70}")
        print(f"🏙️  Scraping: {location_name}")
        if is_barcelona_neighborhood:
            print(f"    (Barcelona neighborhood)")
        print(f"{'='*70}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config['headless'])
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Build search query
            if is_barcelona_neighborhood:
                search_query = f"restaurants in {location_name}, Barcelona"
            else:
                search_query = f"restaurants in {location_name}, {location_info.get('province', '')}"
            
            search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            
            print(f"🔍 Loading search results...")
            page.goto(search_url, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            
            # Handle cookie consent
            self.handle_cookie_consent(page)
            
            # Scroll to load all results - IMPROVED VERSION
            print(f"📜 Scrolling to load all results...")
            feed_selector = 'div[role="feed"]'
            
            try:
                page.wait_for_selector(feed_selector, timeout=10000)
            except:
                print("❌ Could not find results feed")
                browser.close()
                return []
            
            # IMPROVED SCROLLING STRATEGY
            previous_count = 0
            no_change_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 100  # Increased from 30
            
            print(f"  Starting aggressive scrolling...")
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll to bottom
                page.evaluate('''
                    (selector) => {
                        const element = document.querySelector(selector);
                        if (element) {
                            element.scrollTo(0, element.scrollHeight);
                        }
                    }
                ''', feed_selector)
                
                # Wait for new content to load
                page.wait_for_timeout(2000)  # Increased wait time
                
                # Count current number of restaurant links
                current_links = page.locator('a[href*="/maps/place/"]').count()
                
                # Check if we found new results
                if current_links > previous_count:
                    print(f"  📍 Found {current_links} restaurants so far...")
                    previous_count = current_links
                    no_change_count = 0
                else:
                    no_change_count += 1
                
                # Check for "end of results" indicators
                try:
                    # Look for text indicating end of results
                    end_indicators = [
                        page.locator('text="You\'ve reached the end of the list"').first,
                        page.locator('text="Has llegado al final de la lista"').first,
                        page.locator('text="Has arribat al final de la llista"').first,
                    ]
                    
                    for indicator in end_indicators:
                        if indicator.is_visible(timeout=500):
                            print(f"  ✅ Reached end of results")
                            break
                except:
                    pass
                
                # Stop if no new results after 5 attempts
                if no_change_count >= 5:
                    print(f"  ⚠️  No new results after {no_change_count} attempts, stopping scroll")
                    break
                
                scroll_attempts += 1
                
                # Progress indicator every 10 scrolls
                if scroll_attempts % 10 == 0:
                    print(f"  🔄 Scrolled {scroll_attempts} times, {current_links} restaurants found...")
            
            print(f"  ✅ Scrolling complete after {scroll_attempts} attempts")
            
            # Collect all restaurant links
            print(f"🔗 Collecting all restaurant links...")
            links = page.locator('a[href*="/maps/place/"]').all()
            restaurant_urls = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/maps/place/' in href and href not in restaurant_urls:
                        restaurant_urls.append(href)
                except:
                    continue
            
            print(f"✅ Found {len(restaurant_urls)} unique restaurants")
            
            # Scrape each restaurant
            location_restaurants = []
            media_folder_counter = 0  # Counter for media_folder
            
            for idx, url in enumerate(restaurant_urls, 1):
                print(f"\n[{idx}/{len(restaurant_urls)}] Scraping restaurant...")
                
                # Pass location_info for neighborhood handling
                scrape_location_info = location_info.copy()
                if is_barcelona_neighborhood:
                    scrape_location_info['neighborhood'] = location_name
                else:
                    scrape_location_info['neighborhood'] = ''
                
                restaurant_data = self.scrape_restaurant_details(page, url, scrape_location_info)
                
                if restaurant_data and restaurant_data['name']:
                    # Check if town name is in the address
                    town_name = location_info.get('city', location_info.get('name', '')).lower()
                    street_address = restaurant_data.get('street', '').lower()
                    
                    if town_name in street_address:
                        # Increment counter and set media_folder
                        media_folder_counter += 1
                        restaurant_data['media_folder'] = f"s{media_folder_counter:02d}"
                        
                        location_restaurants.append(restaurant_data)
                        print(f"  ✅ {restaurant_data['name']} (media: {restaurant_data['media_folder']})")
                    else:
                        print(f"  ⚠️  Skipped: Town name '{town_name}' not in address '{street_address[:50]}...'")
                else:
                    print(f"  ⚠️  Skipped (incomplete data)")
                
                # Delay between restaurants
                page.wait_for_timeout(self.config['between_restaurants_delay'])
            
            browser.close()
            
            print(f"\n✅ Scraped {len(location_restaurants)} restaurants from {location_name}")
            return location_restaurants
    
    def scrape_restaurant_details(self, page, url, location_info):
        """Scrape detailed info from a restaurant page - FIXED VERSION"""
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=10000)
            page.wait_for_timeout(1500)
            
            restaurant = self.create_restaurant_template(location_info)
            
            # FIXED: Extract coordinates from the ACTUAL page URL (after redirect)
            lat, lon = self.extract_coordinates_from_url(page.url)
            restaurant['lat'] = lat
            restaurant['lon'] = lon
            
            if not lat or not lon:
                print(f"  ⚠️  Could not extract coordinates")
            
            # Name
            try:
                name_element = page.locator('h1').first
                restaurant['name'] = name_element.text_content().strip() or ''
            except:
                print(f"  ⚠️  Could not find name")
                restaurant['name'] = ''
            
            # FIXED: Rating and Reviews - Strategy 1 (aria-label)
            try:
                rating_container = page.locator('[aria-label*="stars"]').first
                
                if rating_container.is_visible(timeout=2000):
                    aria_text = rating_container.get_attribute('aria-label') or ''
                    
                    # Extract rating (convert 0-5 to 0-10)
                    rating_match = re.search(r'(\d+\.?\d*)\s*star', aria_text, re.IGNORECASE)
                    if rating_match:
                        rating_value = float(rating_match.group(1))
                        restaurant['score'] = round(rating_value * 2, 1)
                    
                    # Extract review count from same aria-label
                    review_match = re.search(r'([\d,]+)\s*review', aria_text, re.IGNORECASE)
                    if review_match:
                        num_str = review_match.group(1).replace(',', '')
                        restaurant['num_opinions'] = int(num_str)
                    
                    if restaurant['score']:
                        print(f"  ✅ Score: {restaurant['score']}, Reviews: {restaurant['num_opinions']}")
            except:
                pass
            
            # Strategy 2: Fallback if Strategy 1 failed
            if not restaurant['score']:
                try:
                    # Find rating number (4.5, 4.2, etc.)
                    rating_candidates = page.locator('span').all()
                    
                    for candidate in rating_candidates[:20]:
                        try:
                            text = candidate.text_content().strip()
                            # Match pattern like "4.5" or "4,5"
                            if re.match(r'^[1-5][.,]\d$', text):
                                rating_value = float(text.replace(',', '.'))
                                restaurant['score'] = round(rating_value * 2, 1)
                                
                                # Look for reviews in parent container
                                try:
                                    parent = candidate.locator('..').locator('..').first
                                    parent_text = parent.text_content()
                                    
                                    # Look for review count patterns
                                    review_patterns = [
                                        r'(\d+(?:[.,]\d+)?)\s*(?:K|k)?\s*(?:reseñ|review|opinion)',
                                        r'\((\d+(?:[.,]\d+)?)\s*(?:K|k)?\)',
                                    ]
                                    
                                    for pattern in review_patterns:
                                        match = re.search(pattern, parent_text, re.IGNORECASE)
                                        if match:
                                            num_str = match.group(1).replace(',', '').replace('.', '')
                                            # Handle "K" notation (1.2K = 1200)
                                            if 'K' in parent_text or 'k' in parent_text:
                                                restaurant['num_opinions'] = int(float(num_str) * 1000)
                                            else:
                                                restaurant['num_opinions'] = int(num_str)
                                            break
                                except:
                                    pass
                                
                                print(f"  ✅ Score: {restaurant['score']}, Reviews: {restaurant['num_opinions']}")
                                break
                        except:
                            continue
                except:
                    pass
            
            # Price range
            try:
                # Look for spans containing € symbol with price patterns
                # Format: "€30–40" or "€20-30" or "€15-20"
                price_candidates = page.locator('span:has-text("€")').all()
                
                print(f"  🔍 Found {len(price_candidates)} spans with €")
                
                for idx, candidate in enumerate(price_candidates[:50]):  # Check up to 50 candidates
                    try:
                        text = candidate.text_content().strip()
                        
                        # Skip if text is too long (price should be short like "€30–40")
                        if len(text) > 20:
                            continue
                        
                        # Match patterns like "€30–40", "€20-30", "€15"
                        price_pattern = r'€\s*(\d+)\s*[-–—]\s*(\d+)|€\s*(\d+)'
                        match = re.search(price_pattern, text)
                        
                        if match:
                            if match.group(3):  # Single price "€15"
                                restaurant['price'] = f"€{match.group(3)}"
                            else:  # Range "€30–40"
                                restaurant['price'] = f"{match.group(1)}-{match.group(2)}€"
                            print(f"  ✅ Price: {restaurant['price']} (found in candidate #{idx})")
                            break
                    except Exception as e:
                        continue
                
                if not restaurant['price']:
                    print(f"  ⚠️  No price found after checking {min(50, len(price_candidates))} candidates")
            except Exception as e:
                print(f"  ⚠️  Price extraction error: {e}")
            
            # Address
            try:
                address_candidates = [
                    page.locator('button[data-item-id="address"]').first,
                    page.locator('button[aria-label*="Address"]').first,
                    page.locator('button[aria-label*="Dirección"]').first,
                    page.locator('button[aria-label*="Adreça"]').first,
                ]
                
                for candidate in address_candidates:
                    try:
                        if candidate.is_visible(timeout=1000):
                            # Get address and clean it (remove newlines, extra spaces)
                            address = candidate.text_content().strip() or ''
                            # Replace newlines and multiple spaces with single space
                            address = re.sub(r'\s+', ' ', address)
                            restaurant['street'] = address
                            break
                    except:
                        continue
            except:
                pass
            
            # Phone
            try:
                phone_candidates = [
                    page.locator('button[data-item-id*="phone"]').first,
                    page.locator('button[aria-label*="Phone"]').first,
                    page.locator('button[aria-label*="Teléfono"]').first,
                    page.locator('button[aria-label*="Telèfon"]').first,
                ]
                
                for candidate in phone_candidates:
                    try:
                        if candidate.is_visible(timeout=1000):
                            phone_aria = candidate.get_attribute('aria-label') or ''
                            phone_text = candidate.text_content() or ''
                            
                            phone_match = re.search(r'[\+\d][\d\s]+', phone_aria + ' ' + phone_text)
                            if phone_match:
                                phone = phone_match.group().strip()
                                phone = re.sub(r'\s+', '', phone)  # Remove all spaces
                                
                                # Add +34 prefix if not present
                                if not phone.startswith('+'):
                                    phone = '+34 ' + phone
                                
                                restaurant['contact'] = phone
                                break
                    except:
                        continue
            except:
                pass
            
            # Website
            try:
                website_candidates = [
                    page.locator('a[data-item-id="authority"]').first,
                    page.locator('a[aria-label*="Website"]').first,
                    page.locator('a[aria-label*="Sitio web"]').first,
                ]
                
                for candidate in website_candidates:
                    try:
                        if candidate.is_visible(timeout=1000):
                            href = candidate.get_attribute('href') or ''
                            
                            # Clean Google redirect URL
                            if '/url?q=' in href:
                                # Extract actual URL from Google redirect: /url?q=ACTUAL_URL&...
                                match = re.search(r'/url\?q=([^&]+)', href)
                                if match:
                                    href = match.group(1)
                                    # URL decode if needed
                                    from urllib.parse import unquote
                                    href = unquote(href)
                            
                            # Ensure it's a valid URL
                            if href and (href.startswith('http://') or href.startswith('https://')):
                                restaurant['website'] = href
                                break
                    except:
                        continue
            except:
                pass
            
            # FIXED: Opening hours
            try:
                parsed_schedule = self.extract_opening_hours(page)
                if parsed_schedule:
                    restaurant['opening_schedule'] = parsed_schedule
                    print(f"  ✅ Parsed opening hours")
            except Exception as e:
                pass
            
            return restaurant
            
        except Exception as e:
            print(f"  ❌ Error scraping {url}: {e}")
            return None

    def extract_opening_hours(self, page):
        """Extract opening hours using data-value from copy buttons"""
        try:
            schedule = {
                'timezone': 'Europe/Madrid',
                'weekly': {},
                'exceptions': [{'date': '2025-12-25', 'closed': True}]
            }
            
            # STEP 1: Find and click the hours expander button
            # Look for button/div with aria-label containing "Hours" or "Show open hours"
            hours_expander_selectors = [
                '[aria-label*="Show open hours"]',
                '[aria-label*="Hours"][role="button"]',
                'span[aria-label="Hours"]',
                'button[data-item-id="oh"]',
            ]
            
            hours_expanded = False
            for selector in hours_expander_selectors:
                try:
                    expander = page.locator(selector).first
                    if expander.is_visible(timeout=1000):
                        # Check if already expanded
                        parent = expander.locator('..').first
                        aria_expanded = parent.get_attribute('aria-expanded')
                        
                        if aria_expanded != 'true':
                            # Need to click to expand
                            expander.click()
                            page.wait_for_timeout(1000)
                        
                        hours_expanded = True
                        break
                except:
                    continue
            
            # If we couldn't find the expander, the hours might already be visible
            # Continue anyway to try to find the table
            
            # STEP 2: Find all copy buttons with data-tooltip="Copy open hours"
            # These buttons have data-value with the schedule like "Wednesday, 9 am–5 pm"
            
            days_map = {
                'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
                'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun',
                'lunes': 'mon', 'martes': 'tue', 'miércoles': 'wed', 'miercoles': 'wed',
                'jueves': 'thu', 'viernes': 'fri', 'sábado': 'sat', 'sabado': 'sat', 'domingo': 'sun',
                'dilluns': 'mon', 'dimarts': 'tue', 'dimecres': 'wed',
                'dijous': 'thu', 'divendres': 'fri', 'dissabte': 'sat', 'diumenge': 'sun'
            }
            
            # Find all buttons with data-tooltip (stable attribute)
            copy_buttons = page.locator('button[data-tooltip="Copy open hours"]').all()
            
            # Also try other variations
            if len(copy_buttons) == 0:
                copy_buttons = page.locator('button[data-value*=","]').all()  # Buttons with day + time format
            
            if len(copy_buttons) == 0:
                print("  ⚠️  No schedule buttons found")
                return None
            
            print(f"  📅 Found {len(copy_buttons)} schedule buttons")
            
            # STEP 3: Parse each button's data-value
            for button in copy_buttons:
                try:
                    # Get the data-value attribute: "Wednesday, 9 am–5 pm" or "Monday, Closed"
                    data_value = button.get_attribute('data-value')
                    
                    if not data_value:
                        continue
                    
                    # Find which day this is
                    day_code = None
                    for day_name, code in days_map.items():
                        if day_name in data_value.lower():
                            day_code = code
                            break
                    
                    if not day_code:
                        continue
                    
                    # Check if closed
                    if 'closed' in data_value.lower() or 'cerrado' in data_value.lower():
                        schedule['weekly'][day_code] = [{'closed': True}]
                        continue
                    
                    # Extract times: "Wednesday, 9 am–5 pm" or "Thursday, 9 am–12 pm, 1–5 pm"
                    # Remove the day name
                    time_part = data_value
                    for day_name in days_map.keys():
                        time_part = re.sub(f'^{day_name},\\s*', '', time_part, flags=re.IGNORECASE)
                    
                    # Split by comma to get multiple time ranges
                    time_parts = [p.strip() for p in time_part.split(',') if p.strip()]
                    time_ranges = []
                    
                    for part in time_parts:
                        parsed = self.parse_time_range(part)
                        if parsed:
                            time_ranges.append(parsed)
                    
                    if time_ranges:
                        schedule['weekly'][day_code] = time_ranges
                        print(f"  ✅ {day_code}: {len(time_ranges)} time slot(s)")
                    else:
                        schedule['weekly'][day_code] = [{'closed': True}]
                        
                except Exception as e:
                    print(f"  ⚠️  Error parsing button: {e}")
                    continue
            
            # Fill missing days as closed
            for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                if day not in schedule['weekly']:
                    schedule['weekly'][day] = [{'closed': True}]
            
            # Check if we got any real data (at least one day not closed)
            has_data = any(
                not (len(times) == 1 and times[0].get('closed'))
                for times in schedule['weekly'].values()
            )
            
            if has_data:
                print(f"  ✅ Successfully parsed opening hours")
                return schedule
            else:
                print(f"  ⚠️  All days marked as closed")
                return None
            
        except Exception as e:
            print(f"  ❌ Error extracting hours: {e}")
            return None

    def parse_time_range(self, time_text):
        """Parse a time range string into start/end times in 24h format"""
        try:
            time_text = time_text.lower().strip()
            
            # Remove "to" words - replace with hyphen for consistent parsing
            time_text = re.sub(r'\b(to|a|à)\b', '-', time_text)
            
            # Handle 24 hours
            if any(phrase in time_text for phrase in ['24 hour', 'open 24', 'abierto 24', 'obert 24']):
                return {'start': '00:00', 'end': '23:59'}
            
            # Handle closed
            if any(word in time_text for word in ['closed', 'cerrado', 'tancat']):
                return None
            
            # Pattern 1: "2–6 am" (same period for both)
            pattern1 = r'(\d{1,2})(?::(\d{2}))?\s*[-–—]\s*(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)'
            match = re.search(pattern1, time_text, re.IGNORECASE)
            
            if match:
                start_h, start_m, end_h, end_m, period = match.groups()
                start_hour = int(start_h)
                end_hour = int(end_h)
                start_min = int(start_m) if start_m else 0
                end_min = int(end_m) if end_m else 0
                
                if 'p' in period.lower():
                    if start_hour != 12:
                        start_hour += 12
                    if end_hour != 12:
                        end_hour += 12
                elif 'a' in period.lower():
                    if start_hour == 12:
                        start_hour = 0
                    if end_hour == 12:
                        end_hour = 0
                
                return {
                    'start': f"{start_hour:02d}:{start_min:02d}",
                    'end': f"{end_hour:02d}:{end_min:02d}"
                }
            
            # Pattern 2: "1:00 PM - 11:00 PM" or "13:00-23:00" or "4:30-8 pm"
            pattern2 = r'(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?[\s\-–—]+(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?'
            match = re.search(pattern2, time_text, re.IGNORECASE)
            
            if match:
                start_h, start_m, start_p, end_h, end_m, end_p = match.groups()
                
                start_hour = int(start_h)
                end_hour = int(end_h)
                start_min = int(start_m) if start_m else 0
                end_min = int(end_m) if end_m else 0
                
                # If only end has period and no start period, apply same period to start
                # Example: "4:30-8 pm" should be 4:30 PM - 8:00 PM
                if end_p and not start_p:
                    start_p = end_p
                
                # Convert start time
                if start_p:
                    if 'p' in start_p.lower() and start_hour != 12:
                        start_hour += 12
                    elif 'a' in start_p.lower() and start_hour == 12:
                        start_hour = 0
                
                # Convert end time
                if end_p:
                    if 'p' in end_p.lower() and end_hour != 12:
                        end_hour += 12
                    elif 'a' in end_p.lower() and end_hour == 12:
                        end_hour = 0
                
                return {
                    'start': f"{start_hour:02d}:{start_min:02d}",
                    'end': f"{end_hour:02d}:{end_min:02d}"
                }
            
            return None
            
        except:
            return None
    
    def save_to_yaml(self, restaurants, location_name):
        """Save restaurants to YAML file with Cookiefy format - proper flow style for schedules"""
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        
        filename = location_name.lower().replace(' ', '_').replace('-', '_')
        filepath = output_dir / f"{filename}.yaml"
        
        output_data = {'sites': restaurants}
        
        # Custom YAML dumper for proper formatting
        class CookiefyDumper(yaml.SafeDumper):
            pass
        
        def str_representer(dumper, data):
            # Always use double quotes for strings
            if data.count('\n') > 2:  # Multiple paragraphs only
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
        
        def dict_representer(dumper, data):
            # Use flow style for time slot dicts: { start: "...", end: "..." } or { closed: true }
            if 'start' in data or 'closed' in data or 'date' in data:
                return dumper.represent_mapping('tag:yaml.org,2002:map', data.items(), flow_style=True)
            return dumper.represent_mapping('tag:yaml.org,2002:map', data.items(), flow_style=False)
        
        CookiefyDumper.add_representer(str, str_representer)
        CookiefyDumper.add_representer(dict, dict_representer)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(
                output_data,
                f,
                Dumper=CookiefyDumper,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                width=120,
                indent=2
            )
        
        print(f"💾 Saved to {filepath}")
        return filepath

    def run(self, location_type='towns'):
        """Run scraper for specified location type"""
        locations = LOCATIONS.get(location_type, [])
        
        if not locations:
            print(f"❌ No locations found for type: {location_type}")
            return
        
        print(f"\n{'#'*70}")
        print(f"# COOKIEFY RESTAURANT SCRAPER")
        print(f"# Scraping {len(locations)} locations ({location_type})")
        print(f"{'#'*70}\n")
        
        for idx, location_info in enumerate(locations, 1):
            print(f"\n{'*'*70}")
            print(f"* Location {idx}/{len(locations)}")
            print(f"{'*'*70}")
            
            restaurants = self.scrape_location(location_info)
            
            if restaurants:
                location_name = location_info.get('name', '')
                self.save_to_yaml(restaurants, location_name)
            
            # Delay between locations
            if idx < len(locations):
                delay_seconds = self.config['between_locations_delay'] / 1000
                print(f"\n⏸️  Waiting {delay_seconds}s before next location...")
                import time
                time.sleep(delay_seconds)
        
        print(f"\n{'#'*70}")
        print(f"# ✅ COMPLETE!")
        print(f"# Check the '{OUTPUT_DIR}/' folder for YAML files")
        print(f"{'#'*70}\n")


def main():
    """Main entry point"""
    import sys
    
    scraper = CookiefyRestaurantScraper()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        location_type = sys.argv[1]
    else:
        # Interactive menu
        print("\n" + "="*50)
        print("COOKIEFY RESTAURANT SCRAPER")
        print("="*50)
        print("\nSelect location type to scrape:")
        print("1. Towns (Queixans, Puigcerdà, etc.)")
        print("2. Barcelona neighborhoods")
        print("3. All locations")
        print("\nOr press Ctrl+C to exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            location_type = 'towns'
        elif choice == '2':
            location_type = 'barcelona_neighborhoods'
        elif choice == '3':
            location_type = 'all'
        else:
            print("Invalid choice")
            return
    
    # Run scraper
    if location_type == 'all':
        scraper.run('towns')
        scraper.run('barcelona_neighborhoods')
    else:
        scraper.run(location_type)


if __name__ == "__main__":
    main()