# scraper.py

from playwright.sync_api import sync_playwright
import re

def scrape_page(page, url):
    try:

        mls_match = re.search(r'mls-(\w+)/', url)
        mls = mls_match.group(1) if mls_match else 'N/A'
        # Navigate to the target URL
        page.goto(url, timeout=60000)  # 60 seconds timeout

        # Wait for the main content to load by waiting for the 'Description' section
        page.wait_for_selector('#details-section', timeout=30000)  # 30 seconds timeout

        # Extract the page title to get initial data like price and address
        title = page.title()
        # Example title: "For Sale $779,000 - 602-8188 FRASER STREET, Vancouver, BC | Zealty"
        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', title)
        address_match = re.search(r'-\s*(.*?)\s*\|', title)

        price = price_match.group(1).replace(',', '') if price_match else 'N/A'
        address = address_match.group(1) if address_match else 'N/A'

        # Extract Description using XPath to accurately select the description div
        description_selector = "xpath=//div[@id='details-section']/following-sibling::div[1]"
        description_element = page.query_selector(description_selector)
        description = description_element.inner_text().strip() if description_element else 'N/A'


        # Extract Property Details from the table
        table_selector = 'table.stripedTable tbody'
        table = page.query_selector(table_selector)
        property_details = {}
        if table:
            rows = table.query_selector_all('tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) >= 2:
                    # Extract only the main header text by splitting at newline
                    key_full_text = cells[0].inner_text().strip()
                    key_main = key_full_text.split('\n')[0].lower().replace(' ', '_').replace('/', '_')
                    
                    # Extract only the main value before any line breaks
                    value_full_text = cells[1].inner_text().strip()
                    value_main = value_full_text.split('\n')[0].replace('$', '').strip()
                    
                    property_details[key_main] = value_main

        # Extract Features & Amenities
        features_selector = 'div.section-heading:has-text("Features & Amenities") + div ul.striped.check-bullets'
        features_list = []
        features_ul = page.query_selector(features_selector)
        if features_ul:
            features = features_ul.query_selector_all('li')
            for feature in features:
                feature_text = feature.inner_text().strip()
                features_list.append(feature_text)

        # Extract Images
        images_selector = '#photo-section img.photo-height'
        images = page.query_selector_all(images_selector)
        image_urls = [img.get_attribute('src') for img in images if img.get_attribute('src') and not img.get_attribute('src').startswith('data:image/')]

        # Compile all data
        data = {
            'url': url,
            'listing_price': price,
            'listing_address': address,
            'description': description,
            'mls': mls,
            'bedrooms': property_details.get('bedrooms', 'N/A'),
            'bathrooms': property_details.get('bathrooms', 'N/A'),
            'size': property_details.get('size_of_house', 'N/A'),
            'age': property_details.get('age_of_house', 'N/A'),
            'listing_style': property_details.get('style_of_house', 'N/A'),
            'maintenance_fee': property_details.get('maintenance_fee', 'N/A'),
            'property_taxes': property_details.get('property_taxes', 'N/A'),
            'features_&_amenities': features_list,
            'gallery': image_urls
        }

        return data

    except Exception as e:
        print(f"Error scraping URL {url}: {e}")

