"""
File Name: inspect_instagram.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and checks if an Instagram 
    tab is open.

"""

# CONFIGURATION
from pathlib import Path
from playwright.sync_api import sync_playwright


# Path to Chrome's dynamically generated DevTools endpoint.
DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"


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
    context = browser.contexts[0]

    # Search through all open browser tabs and return if IG found.
    page = None

    for test in context.pages:
        print("TAB:", test.url)

        if "instagram.com" in test.url:
            page = test
            break

    if not page:
        print("Instagram tab not found")
        exit()

    print("\nInstagram found")
    print("URL:", page.url)
    print("TITLE:", page.title())

    input("\nPress ENTER to close...")
