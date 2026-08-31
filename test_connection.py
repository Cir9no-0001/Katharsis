"""
File Name: test_connection.py
Author: Stanley Chen
Date Created: August 30, 2026
Description: 
    Tests the Playwright Chrome DevTools Protocol (CDP) connection by
    attaching to an existing Chrome session and displaying available
    browser contexts and open tabs.
    
"""

from pathlib import Path
from playwright.sync_api import sync_playwright


# Path to Chrome's dynamically generated DevTools endpoint
DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"


with sync_playwright() as p:

    # Read Chrome's active debugging port and WebSocket path
    print("Reading Chrome's debugging endpoint...")
    lines = DEVTOOLS_FILE.read_text().splitlines()
    port = lines[0].strip()
    ws_path = lines[1].strip()

    ws_endpoint = f"ws://127.0.0.1:{port}{ws_path}"
    print(f"Connecting to Chrome on port {port}...")

    # Attach Playwright to the existing Chrome browser session
    browser = p.chromium.connect_over_cdp(ws_endpoint)
    print("Connected to Chrome!")
    print(f"\nContexts found: {len(browser.contexts)}")

    # Display all available browser contexts and open tabs
    for context_index, context in enumerate(browser.contexts):
        print(f"\n--- Context {context_index} ---")

        for page_index, page in enumerate(context.pages):
            print(f"\nTab {page_index}")
            print(f"  URL:   {page.url}")
            print(f"  Title: {page.title()}")

    input("\nPress ENTER to disconnect...")
