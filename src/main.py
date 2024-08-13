"""
Main entry point for the Best Ball Rankings Agent
"""

from web_scraper import main as scraper_main
from data_processor import process_data
from draftkings_uploader import upload_rankings_to_draftkings, load_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import tempfile
import os

def main():
    try:
        # Run the web scraper
        scraped_data = scraper_main()
        
        if scraped_data:
            # Process the scraped data
            processed_data = process_data(scraped_data)
            
            if processed_data is not None:
                logging.info(f"Processed {len(processed_data)} player rankings")
                print(processed_data.head())  # Print the first few rows of processed data
                
                # Load configuration for DraftKings uploader
                config = load_config()

                # Create a temporary CSV file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_csv:
                    processed_data.to_csv(temp_csv.name, index=False)
                    temp_csv_path = temp_csv.name

                # Upload processed data to DraftKings
                if all([config['DRAFTKINGS_USERNAME'], config['DRAFTKINGS_PASSWORD']]):
                    try:
                        upload_rankings_to_draftkings(
                            config['DRAFTKINGS_USERNAME'],
                            config['DRAFTKINGS_PASSWORD'],
                            temp_csv_path
                        )
                        logging.info("Data processing and uploading to DraftKings completed successfully.")
                    finally:
                        # Clean up the temporary file
                        os.unlink(temp_csv_path)
                else:
                    logging.error("Missing required configuration for DraftKings upload. Please check your .env file or environment variables.")
            else:
                logging.warning("Data processing failed.")
        else:
            logging.warning("No data was scraped. Skipping data processing and DraftKings upload.")
    except Exception as e:
        logging.error(f"An error occurred in the main function: {str(e)}")

if __name__ == "__main__":
    main()
