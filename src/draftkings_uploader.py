import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class DraftKingsUploaderError(Exception):
    """Custom exception for DraftKings uploader errors."""
    pass

def login_to_draftkings(page, username, password):
    """Log in to DraftKings."""
    try:
        page.goto("https://myaccount.draftkings.com/login?returnPath=%2flobby")
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
    except PlaywrightTimeoutError:
        raise DraftKingsUploaderError("Login to DraftKings failed.")

def navigate_to_rankings_page(page):
    """Navigate to the rankings upload page."""
    try:
        page.goto("https://www.draftkings.com/draft/rankings/nfl")
        page.wait_for_load_state('networkidle')
    except PlaywrightTimeoutError:
        raise DraftKingsUploaderError("Navigation to rankings page failed.")

def upload_csv_file(page, file_path):
    """Upload the CSV file to DraftKings."""
    try:
        page.click('button[data-testid="csv-upload-download"]')
        page.click('text="UPLOAD CSV"')
        
        with page.expect_file_chooser() as fc_info:
            page.click('text="Choose File"')
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)
        
        page.click('text="Upload"')
        page.wait_for_selector('text="Pre-Draft Rankings CSV uploaded successfully! Please remember to save your rankings."')
    except PlaywrightTimeoutError:
        raise DraftKingsUploaderError("CSV file upload failed.")

def save_rankings(page):
    """Save the uploaded rankings."""
    try:
        page.click('text="SAVE RANKINGS"')
        page.wait_for_selector('text="Your rankings have been saved successfully."')
    except PlaywrightTimeoutError:
        raise DraftKingsUploaderError("Saving rankings failed.")

def upload_rankings_to_draftkings(username, password, csv_file_path):
    """Main function to upload rankings to DraftKings."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login_to_draftkings(page, username, password)
            navigate_to_rankings_page(page)
            upload_csv_file(page, csv_file_path)
            save_rankings(page)
            logging.info("Rankings uploaded and saved successfully.")
        except DraftKingsUploaderError as e:
            logging.error(f"Error uploading rankings: {str(e)}")
        finally:
            browser.close()

if __name__ == "__main__":
    # This block can be used for testing the module
    import os
    from dotenv import load_dotenv

    load_dotenv()
    username = os.getenv("DRAFTKINGS_USERNAME")
    password = os.getenv("DRAFTKINGS_PASSWORD")
    csv_file_path = "path/to/your/csv/file.csv"

    upload_rankings_to_draftkings(username, password, csv_file_path)
