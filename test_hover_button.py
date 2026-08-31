"""
File Name: test_hover_button.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and tests Instagram's
    message action menu detection by hovering over a message and locating
    available options.
    
"""

# CONFIGURATION
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os


# Path to Chrome's dynamically generated DevTools endpoint
DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"


# Load environment username variable
load_dotenv()
USERNAME = os.getenv(
    "INSTAGRAM_USERNAME"
)

# MAIN
with sync_playwright() as p:
    # Connect to an existing Chrome session through CDP
    lines = DEVTOOLS_FILE.read_text().splitlines()
    ws_endpoint = (
        f"ws://127.0.0.1:{lines[0]}"
        f"{lines[1]}"
    )

    # Connects to an already-running Chrome instance to avoid storing credentials or session cookies
    browser = p.chromium.connect_over_cdp(ws_endpoint)
    page = browser.contexts[0].pages[0]

    # Pick the first visible message
    message = page.locator("div[dir='auto']").first
    print("Hovering over:", message.inner_text())
    message.hover()

    # Wait for IG to show the button
    options_button = page.locator(
        f"svg[aria-label='See more options for message from {USERNAME}']")

    options_button.first.wait_for(timeout=5000)

    print("Three-dot button detected!")
    print("Clicking three dots...")
    options_button.first.click()
    print("Waiting for menu...")

    page.wait_for_timeout(1000)

    unsend = page.get_by_role("button", name="Unsend")

    print("Unsend buttons found:", unsend.count())

    if unsend.count() > 0:
        print("Unsend menu item detected!")
    else:
        print("Unsend not found")

    input("Press ENTER to close...")
