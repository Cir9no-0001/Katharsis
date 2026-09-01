"""
File Name: scan_unsend.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and scans Instagram messages
    to identify messages with available unsend actions.
    
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


with sync_playwright() as p:
    # Connect to an existing Chrome session through CDP
    lines = DEVTOOLS_FILE.read_text().splitlines()
    ws = f"ws://127.0.0.1:{lines[0]}{lines[1]}"

    # Connects to an already-running Chrome instance to avoid storing credentials or session cookies
    browser = p.chromium.connect_over_cdp(ws)
    page = browser.contexts[0].pages[0]

    # Locate visible IG messages on the current page
    messages = page.locator("div[dir='auto']")
    print("Messages:", messages.count())

    # Check each message for unsend button in triple dot button
    for i in range(min(messages.count(), 12)):
        msg = messages.nth(i)
        text = msg.inner_text().strip()

        if not text:
            continue

        print("\n===================")
        print("Checking:", text[:60])

        msg.hover()

        page.wait_for_timeout(700)

        found = False
        parent = msg

        for level in range(10):
            parent = parent.locator("..")
            options = parent.locator(
                f"svg[aria-label='See more options for message from {USERNAME}']"
            )

            if options.count():
                print("Found local options at parent level:", level + 1)
                options.first.click()
                found = True
                break

        if not found:
            print("No local options button found")
            continue

        page.wait_for_timeout(500)
        unsend = page.get_by_role(
            "button",
            name="Unsend"
        )

        if unsend.count():
            print("This message has Unsend")
        else:
            print("No Unsend")

        page.keyboard.press("Escape")
