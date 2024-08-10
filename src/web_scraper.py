"""
Web Scraper Module

This module handles web scraping functionality using Playwright.
"""

import os
import csv
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_page_content(page):
    """
    Print the current page content for debugging purposes.
    """
    logging.info("Current page content:")
    content = page.content()
    print(content[:1000])  # Print first 1000 characters to avoid overwhelming the console
    logging.info("End of page content")

def login(context, username, password):
    """
    Log in to the website using provided credentials.

    Args:
        context: Playwright browser context
        username (str): Username for login
        password (str): Password for login

    Returns:
        Page: Logged in page object

    Raises:
        Exception: If login fails
    """
    try:
        page = context.new_page()
        logging.info("Navigating to login page")
        page.goto("https://establishtherun.com/wp-login.php", timeout=60000)  # Increase timeout to 60 seconds
        
        logging.info("Filling in login credentials")
        page.fill('input[name="log"]', username)
        page.fill('input[name="pwd"]', password)
        
        logging.info("Submitting login form")
        page.click('input[name="wp-submit"]')
        
        logging.info("Waiting for navigation after login")
        page.wait_for_load_state("networkidle", timeout=60000)  # Increase timeout to 60 seconds

        # Check for error messages
        error_message = page.query_selector('.login .message')
        if error_message:
            error_text = error_message.inner_text()
            logging.error(f"Login error message: {error_text}")
            raise Exception(f"Login failed: {error_text}")

        # Check if we're still on the login page
        if "wp-login.php" in page.url:
            # Check for specific error messages on the login page
            login_error = page.query_selector('#login_error')
            if login_error:
                error_text = login_error.inner_text()
                logging.error(f"Login error: {error_text}")
                print_page_content(page)
                raise Exception(f"Login failed: {error_text}")
            else:
                logging.error(f"Still on login page. Current URL: {page.url}")
                print_page_content(page)
                raise Exception("Login failed: Redirected back to login page")

        # Check if we're on the wp-admin page or any other page within the site
        if not (page.url.startswith("https://establishtherun.com/wp-admin") or 
                page.url.startswith("https://establishtherun.com/")):
            logging.error(f"Unexpected redirect. Current URL: {page.url}")
            raise Exception(f"Login failed: Unexpected redirect to {page.url}")
        
        logging.info(f"Login successful. Current URL: {page.url}")

        # Set cookies explicitly after successful login
        cookies = context.cookies()
        logging.info(f"Number of cookies after login: {len(cookies)}")
        for cookie in cookies:
            logging.info(f"Cookie: {cookie['name']} = {cookie['value']}")

        # Additional check: Try to access a protected resource
        try:
            logging.info("Attempting to access a protected resource")
            page.goto("https://establishtherun.com/wp-admin/", timeout=30000)
            if "wp-login.php" in page.url:
                logging.error("Failed to access protected resource. Redirected to login page.")
                raise Exception("Login seems successful, but unable to access protected resources")
            logging.info("Successfully accessed protected resource")
        except PlaywrightTimeoutError:
            logging.error("Timeout while accessing protected resource")
            raise Exception("Login seems successful, but timed out while accessing protected resources")
        
        return page
    except PlaywrightTimeoutError as e:
        logging.error(f"Login timed out: {str(e)}")
        raise Exception(f"Login timed out: {str(e)}")
    except Exception as e:
        logging.error(f"An error occurred during login: {str(e)}")
        raise

def fetch_player_rankings(page, url):
    """
    Fetch player rankings from the specified URL using Playwright.

    Args:
        page: Playwright page object
        url (str): The URL of the rankings page.

    Returns:
        list[dict]: A list of dictionaries containing player information.
    """
    try:
        page.goto(url)
        page.wait_for_selector('table[data-ninja_table_instance="ninja_table_instance_0"]')

        players = page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('table[data-ninja_table_instance="ninja_table_instance_0"] tbody tr'));
                return rows.map(row => {
                    const cells = row.querySelectorAll('td');
                    return {
                        rank: cells[0].textContent.trim(),
                        name: cells[1].textContent.trim(),
                        position: cells[2].textContent.trim(),
                        team: cells[3].textContent.trim(),
                        bye_week: cells[4].textContent.trim(),
                        best_ball_points: cells[5].textContent.trim()
                    };
                });
            }
        """)
        return players
    except PlaywrightTimeoutError:
        raise Exception("Failed to load rankings page")

def download_csv(page, url, output_path):
    """
    Download the CSV file from the rankings page.

    Args:
        page: Playwright page object
        url (str): The URL of the rankings page
        output_path (str): The path to save the downloaded CSV

    Raises:
        Exception: If CSV download fails
    """
    try:
        page.goto(url)
        with page.expect_download() as download_info:
            page.click('a.ninja-forms-field[href*=".csv"]')
        download = download_info.value
        download.save_as(output_path)
    except PlaywrightTimeoutError:
        raise Exception("CSV download timed out")

def main():
    url = "https://establishtherun.com/etrs-top-300-for-draftkings-best-ball-rankings-updates-9am-daily/"
    username = os.environ.get("ETR_USERNAME")
    password = os.environ.get("ETR_PASSWORD")
    csv_output_path = "rankings.csv"

    if not username or not password:
        raise ValueError("ETR_USERNAME and ETR_PASSWORD environment variables must be set")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            java_script_enabled=True,
            ignore_https_errors=True,
            has_touch=False,
            is_mobile=False,
            locale='en-US',
        )

        # Enable cookies
        context.add_cookies([{
            'name': 'wordpress_test_cookie',
            'value': 'WP Cookie check',
            'domain': 'establishtherun.com',
            'path': '/',
        }])

        try:
            page = login(context, username, password)
            rankings = fetch_player_rankings(page, url)
            download_csv(page, url, csv_output_path)

            print(f"Fetched {len(rankings)} player rankings")
            print(rankings[:5])  # Print the first 5 rankings as a sample
            print(f"CSV file downloaded to {csv_output_path}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
