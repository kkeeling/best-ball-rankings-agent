"""
Main entry point for the Best Ball Rankings Agent
"""

from web_scraper import main as scraper_main
from data_processor import process_data
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        # Run the web scraper
        scraped_data = scraper_main()
        
        if scraped_data:
            # Process the scraped data
            processed_data = process_data(scraped_data)
            
            # TODO: Add code to save or further process the data
            logging.info(f"Processed {len(processed_data)} player rankings")
            print(processed_data.head())  # Print the first few rows of processed data
        else:
            logging.warning("No data was scraped. Skipping data processing.")
    except Exception as e:
        logging.error(f"An error occurred in the main function: {str(e)}")

if __name__ == "__main__":
    main()
