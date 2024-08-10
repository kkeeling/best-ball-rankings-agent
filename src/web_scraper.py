"""
Web Scraper Module

This module handles web scraping functionality using Playwright.
"""

import os
import csv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def login(page, username, password):
    """
    Log in to the website using provided credentials.

    Args:
        page: Playwright page object
        username (str): Username for login
        password (str): Password for login

    Raises:
        Exception: If login fails
    """
    try:
        page.goto("https://establishtherun.com/wp-login.php")
        page.fill('input[name="log"]', username)
        page.fill('input[name="pwd"]', password)
        page.click('input[name="wp-submit"]')
        page.wait_for_load_state("networkidle")

        if "wp-admin" not in page.url:
            raise Exception("Login failed")
    except PlaywrightTimeoutError:
        raise Exception("Login timed out")

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
        page = browser.new_page()

        try:
            login(page, username, password)
            rankings = fetch_player_rankings(page, url)
            download_csv(page, url, csv_output_path)

            print(f"Fetched {len(rankings)} player rankings")
            print(rankings[:5])  # Print the first 5 rankings as a sample
            print(f"CSV file downloaded to {csv_output_path}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
