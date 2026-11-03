"""
File Name: test_hover.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and inspects visible
    Instagram message elements for debugging and selector testing.
    
"""

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

    print("Current page:", page.url)

    # Find and print all visible messages
    messages = page.locator("div[dir='auto']")

    print("Visible text elements:", messages.count())

    for i in range(messages.count()):
        text = messages.nth(i).inner_text().strip()

        if text:
            print(i, repr(text[:80]))

    input("Press ENTER to close...")
