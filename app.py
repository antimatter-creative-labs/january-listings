# app.py

import subprocess
import streamlit as st
import pandas as pd
from scraper import scrape_page
from playwright.async_api import async_playwright

# Define ACF field names and their corresponding data extraction
ACF_FIELD_MAPPING = {
    "listing_price": "listing_price",
    "listing_address": "listing_address",
    "description": "description",
    "mls": "mls",
    "bedrooms": "bedrooms",
    "bathrooms": "bathrooms",
    "size": "size",
    "age": "age",
    "listing_style": "listing_style",
    "maintenance_fee": "maintenance_fee",
    "property_taxes": "property_taxes",
    "features_&_amenities": "features_&_amenities",
    "gallery": "gallery"
}

# Define possible choices for 'type' and 'subtype' to validate or map scraped data
TYPE_CHOICES = {
    "House": "House",
    "Condo/Townhouse": "Condo/Townhouse",
    "Land Only": "Land Only",
    "Apartment": "Apartment"
}

SUBTYPE_CHOICES = {
    "House/Single Family": "House/Single Family",
    "Apartment/Condo": "Apartment/Condo",
    "Townhouse": "Townhouse",
    "1_2_Duplex": "1/2 Duplex",
    "Manufactured_with_Land": "Manufactured with Land",
    "Corner Unit": "Corner Unit"
}

def convert_to_csv(data_list):
    if not data_list:
        return ""
    
    records = []
    for data in data_list:
        if 'error' in data:
            # Handle entries with errors by leaving ACF fields blank
            record = {acf_field: "" for acf_field in ACF_FIELD_MAPPING.keys()}
            record['url'] = data.get('url', '')
            record['error'] = data.get('error', '')
        else:
            record = {}
            # Map scraped data to ACF fields
            for acf_field, scraped_field in ACF_FIELD_MAPPING.items():
                if scraped_field in data and data[scraped_field]:
                    value = data[scraped_field]
                    # Handle specific field types
                    if acf_field == "features_&_amenities":
                        # Concatenate feature label-value pairs into a string
                        if isinstance(value, list):
                            features_str = "; ".join([f"{feat}" for feat in value if feat])
                            value = features_str
                        else:
                            value = ""
                    elif acf_field in ["listing_style", "ownership_interest"]:
                        # Ensure the value matches one of the ACF choices
                        if acf_field == "listing_style" and value in SUBTYPE_CHOICES:
                            value = SUBTYPE_CHOICES[value]
                        elif acf_field == "ownership_interest" and value in TYPE_CHOICES:
                            value = TYPE_CHOICES[value]
                        else:
                            value = ""  # Leave blank if no match
                    elif acf_field == "gallery":
                        # Join image URLs into a comma-separated string
                        if isinstance(value, list):
                            value = ", ".join(value)
                        else:
                            value = ""
                    else:
                        # For all other fields, leave the value as-is
                        value = value.strip() if isinstance(value, str) else value
                else:
                    value = ""  # Leave blank if field not found or empty
                
                record[acf_field] = value
            
            # Include URL for reference
            record['url'] = data.get('url', '')
            # Optionally, handle 'error' field if desired
            record['error'] = data.get('error', '')
        
        records.append(record)
    
    # Create DataFrame
    df = pd.DataFrame(records)
    return df.to_csv(index=False)

def main():
    st.title("Saretsky Real Estate Listings")
    
    st.write("""
    Enter the URLs of the real estate listings you want to scrape, each on a new line. The app will extract relevant information from each URL. Download the CSV and import it.
    """)
    
    # Multiline text input for multiple URLs
    urls_input = st.text_area(
        "Enter URLs (one per line):",
        ""
    )
    
    if st.button("Scrape and Generate CSV"):
        # Split the input into a list of URLs, stripping whitespace and ignoring empty lines
        urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
        
        if not urls:
            st.error("Please enter at least one valid URL.")
            return
        
        with st.spinner('Scraping data...'):
            data_list = []
            with sync_playwright() as p:
                # Launch the browser once
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                for idx, url in enumerate(urls, start=1):
                    st.write(f"Scraping URL {idx}/{len(urls)}: {url}")
                    data = scrape_page(page, url)
                    data_list.append(data)
                
                # Close the browser after scraping all URLs
                browser.close()
        
        if data_list:
            csv_data = convert_to_csv(data_list)
            st.success("Data scraped and aligned successfully!")
            
            # Provide a download button for the CSV file
            st.download_button(
                label="Download Aggregated CSV",
                data=csv_data,
                file_name='scraped_data.csv',
                mime='text/csv',
            )
            
            # Display the CSV data in a text area for easy copying
            st.text_area("CSV Output:", value=csv_data, height=300)
        else:
            st.error("No data was scraped. Please check the URLs and try again.")

if __name__ == "__main__":
    main()
