import logging
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

# Configure logging
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# Create a file handler
file_handler = logging.FileHandler('draftkings_uploader.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))

# Get the root logger and add the file handler
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

class DraftKingsUploaderError(Exception):
    """Custom exception for DraftKings uploader errors."""
    pass

def login_to_draftkings(page, username, password):
    """Log in to DraftKings."""
    try:
        logging.info("Attempting to log in to DraftKings...")
        page.goto("https://myaccount.draftkings.com/login?returnPath=%2flobby", timeout=60000)
        logging.info("Login page loaded. Filling in credentials...")
        page.fill('input[name="EmailOrUsername"]', username)
        page.fill('input[name="Password"]', password)
        logging.info("Credentials filled. Submitting login form...")
        page.click('button[type="submit"]')
        logging.info("Waiting for login process to complete...")
        
        # Wait for either successful login redirect or error message
        try:
            login_result = page.wait_for_selector('text="Invalid username or password" >> visible=true', timeout=60000, state='attached')
            
            if login_result and login_result.is_visible():
                logging.error("Login failed. Invalid username or password.")
                raise DraftKingsUploaderError("Login to DraftKings failed. Invalid username or password.")
            
            # Check for successful login redirect
            page.wait_for_url("https://www.draftkings.com/lobby", timeout=60000)
            logging.info("Login successful. Redirected to lobby.")
        except PlaywrightTimeoutError:
            logging.error(f"Login process timed out. Current URL: {page.url}")
            logging.error(f"Page title: {page.title()}")
            logging.error(f"Page content: {page.content()}")
            raise DraftKingsUploaderError("Login to DraftKings timed out. Please check the logs for more details.")
        
    except PlaywrightTimeoutError:
        logging.error(f"Timeout occurred. Current URL: {page.url}")
        logging.error(f"Page title: {page.title()}")
        logging.error(f"Page content: {page.content()}")
        raise DraftKingsUploaderError("Login to DraftKings timed out. Please check the logs for more details.")
    except Exception as e:
        logging.error(f"Unexpected error during login: {str(e)}")
        logging.error(f"Current URL: {page.url}")
        logging.error(f"Page title: {page.title()}")
        logging.error(f"Page content: {page.content()}")
        raise DraftKingsUploaderError(f"Login to DraftKings failed: {str(e)}")

def navigate_to_rankings_page(page):
    """Navigate to the rankings upload page."""
    try:
        logging.info("Navigating to rankings page...")
        page.goto("https://www.draftkings.com/draft/rankings/nfl")
        page.wait_for_load_state('networkidle')
        logging.info("Navigation to rankings page successful")
    except PlaywrightTimeoutError:
        logging.error("Navigation to rankings page failed")
        raise DraftKingsUploaderError("Navigation to rankings page failed.")
    except Exception as e:
        logging.error(f"Unexpected error during navigation: {str(e)}")
        raise DraftKingsUploaderError(f"Unexpected error during navigation: {str(e)}")

def upload_csv_file(page, file_path):
    """Upload the CSV file to DraftKings."""
    try:
        logging.info(f"Attempting to upload CSV file: {file_path}")
        page.click('button[data-testid="csv-upload-download"]')
        page.click('text="UPLOAD CSV"')
        
        with page.expect_file_chooser() as fc_info:
            page.click('text="Choose File"')
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)
        
        page.click('text="Upload"')
        page.wait_for_selector('text="Pre-Draft Rankings CSV uploaded successfully! Please remember to save your rankings."', timeout=30000)
        logging.info("CSV file uploaded successfully")
    except PlaywrightTimeoutError:
        logging.error("CSV file upload failed or upload confirmation not received")
        raise DraftKingsUploaderError("CSV file upload failed or upload confirmation not received.")
    except Exception as e:
        logging.error(f"Unexpected error during CSV upload: {str(e)}")
        raise DraftKingsUploaderError(f"Unexpected error during CSV upload: {str(e)}")

def save_rankings(page):
    """Save the uploaded rankings."""
    try:
        logging.info("Attempting to save rankings...")
        page.click('text="SAVE RANKINGS"')
        page.wait_for_selector('text="Your rankings have been saved successfully."')
        logging.info("Rankings saved successfully")
    except PlaywrightTimeoutError:
        logging.error("Saving rankings failed")
        raise DraftKingsUploaderError("Saving rankings failed.")

def upload_rankings_to_draftkings(username, password, csv_file_path):
    """Main function to upload rankings to DraftKings."""
    config = load_config()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.get('HEADLESS', True))
        page = browser.new_page()
        try:
            login_to_draftkings(page, username, password)
            navigate_to_rankings_page(page)
            upload_csv_file(page, csv_file_path)
            save_rankings(page)
            logging.info("Rankings uploaded and saved successfully.")
        except DraftKingsUploaderError as e:
            logging.error(f"Error uploading rankings: {str(e)}")
            raise
        finally:
            browser.close()

def load_config():
    """Load configuration from environment variables or .env file."""
    load_dotenv()
    return {
        'DRAFTKINGS_USERNAME': os.getenv('DRAFTKINGS_USERNAME'),
        'DRAFTKINGS_PASSWORD': os.getenv('DRAFTKINGS_PASSWORD'),
        'CSV_FILE_PATH': os.getenv('CSV_FILE_PATH'),
        'HEADLESS': os.getenv('HEADLESS', 'True').lower() == 'true'
    }

# The main function has been removed as it's no longer necessary.
# The upload_rankings_to_draftkings function is now called directly from src/main.py
