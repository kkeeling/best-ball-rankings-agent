"""
Web Scraper Module

This module handles web scraping functionality using Playwright.
"""

import os
import csv
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebScraperError(Exception):
    """Custom exception class for web scraper errors"""
    pass

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
        WebScraperError: If login fails
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
                raise WebScraperError(f"Login failed: {error_text}")
            else:
                logging.error(f"Still on login page. Current URL: {page.url}")
                print_page_content(page)
                raise WebScraperError("Login failed: Redirected back to login page")

        # Check if we're on the wp-admin page or any other page within the site
        if not (page.url.startswith("https://establishtherun.com/wp-admin") or 
                page.url.startswith("https://establishtherun.com/")):
            logging.error(f"Unexpected redirect. Current URL: {page.url}")
            raise WebScraperError(f"Login failed: Unexpected redirect to {page.url}")
        
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
        raise WebScraperError(f"Login timed out: {str(e)}")
    except PlaywrightError as e:
        logging.error(f"A Playwright error occurred during login: {str(e)}")
        raise WebScraperError(f"A Playwright error occurred during login: {str(e)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during login: {str(e)}")
        raise WebScraperError(f"An unexpected error occurred during login: {str(e)}")

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
                        name: cells[0].textContent.trim(),
                        team: cells[1].textContent.trim(),
                        position: cells[2].textContent.trim(),
                        etr_rank: cells[3].textContent.trim(),
                        etr_pos_rank: cells[4].textContent.trim(),
                        adp: cells[5].textContent.trim(),
                        adp_pos_rank: cells[6].textContent.trim(),
                        adp_diff: cells[7].textContent.trim(),
                    };
                });
            }
        """)
        return players
    except PlaywrightTimeoutError:
        raise Exception("Failed to load rankings page")


def main():
    url = "https://establishtherun.com/etrs-top-300-for-draftkings-best-ball-rankings-updates-9am-daily/"
    username = os.environ.get("ETR_USERNAME")
    password = os.environ.get("ETR_PASSWORD")

    if not username or not password:
        raise WebScraperError("ETR_USERNAME and ETR_PASSWORD environment variables must be set")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
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

                print(f"Fetched {len(rankings)} player rankings")
                print(rankings[:5])  # Print the first 5 rankings as a sample

            except WebScraperError as e:
                logging.error(f"A web scraping error occurred: {str(e)}")
                print(f"A web scraping error occurred: {str(e)}")
            except PlaywrightError as e:
                logging.error(f"A Playwright error occurred: {str(e)}")
                print(f"A Playwright error occurred: {str(e)}")
            finally:
                context.close()
                browser.close()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
