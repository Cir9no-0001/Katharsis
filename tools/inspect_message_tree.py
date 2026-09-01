"""
File Name: inspect_message_tree.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and inspects the DOM structure
    of an Instagram message to locate interactive elements.

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

    # Locate first visible message element and hover over it to trigger action controls
    message = page.locator("div[dir='auto']").first

    print("Hovering:", message.inner_text())

    message.hover()

    # Find the three dots that appear after hovering over a message.
    button = page.locator(
        f"svg[aria-label='See more options for message from {USERNAME}']"
    ).first

    button.wait_for(timeout=5000)

    print("Found options button")

    # Go up the DOM tree to inspect parent containers.
    print("\nWalking UP from button:")

    current = button

    for i in range(8):
        current = current.locator("..")

        print(
            "\nLEVEL",
            i+1,
            current.evaluate("(el)=>el.tagName"),
            "\nTEXT:",
            current.inner_text()[:100]
        )

    input("\nDone")
