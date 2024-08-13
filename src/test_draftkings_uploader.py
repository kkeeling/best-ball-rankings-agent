import argparse
import logging
from draftkings_uploader import upload_rankings_to_draftkings, load_config, DraftKingsUploaderError

def main():
    parser = argparse.ArgumentParser(description="Test DraftKings Uploader")
    parser.add_argument("--csv", help="Path to the CSV file to upload", required=True)
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Load configuration
    config = load_config()

    if not all([config['DRAFTKINGS_USERNAME'], config['DRAFTKINGS_PASSWORD']]):
        logging.error("Missing required configuration. Please check your .env file or environment variables.")
        return

    try:
        upload_rankings_to_draftkings(
            config['DRAFTKINGS_USERNAME'],
            config['DRAFTKINGS_PASSWORD'],
            args.csv
        )
        logging.info("Test completed successfully.")
    except DraftKingsUploaderError as e:
        logging.error(f"Error during test: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during test: {str(e)}")

if __name__ == "__main__":
    main()
