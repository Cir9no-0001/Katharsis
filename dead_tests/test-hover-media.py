"""
File Name: test_hover_media.py
Author: Stanley Chen
Date Created: August 31, 2026
Description:
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and tests Instagram media
    action menu detection by hovering over an image or Reel and locating
    its local three-dot options button.
    
    This test does not delete anything.
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
USERNAME = os.getenv("INSTAGRAM_USERNAME")


with sync_playwright() as p:

    print("Connecting to Chrome...")

    lines = DEVTOOLS_FILE.read_text().splitlines()

    ws_endpoint = (
        f"ws://127.0.0.1:{lines[0]}"
        f"{lines[1]}"
    )

    # Connect to the already-authenticated Chrome session
    browser = p.chromium.connect_over_cdp(
        ws_endpoint
    )

    page = browser.contexts[0].pages[0]
    print("Current page:", page.url)

    media = page.locator("img.x1iyjqo2.x193iq5w.xl1xv1r")

    print("\nMedia elements found:", media.count())

    if media.count() == 0:

        print("No media found")

        input("\nPress ENTER to close...")

        raise SystemExit

    target = None

    for i in range(media.count()):

        candidate = media.nth(i)

        if candidate.is_visible():

            target = candidate

            print(
                f"Using media element: {i}"
            )

            break

    if target is None:
        print("No visible media found")

        input("\nPress ENTER to close...")

        raise SystemExit

    print("\nHovering over media...")

    target.hover()

    page.wait_for_timeout(1000)

    print("\nWalking UP from media...")

    parent = target

    found = False

    for level in range(10):
        parent = parent.locator("..")

        print(f"Checking parent level {level + 1}...")

        options_button = parent.locator(
            f"svg[aria-label='See more options for message from {USERNAME}']")

        if options_button.count():

            print("Three-dot button found at parent level:", level + 1)

            print("Clicking three dots...")

            options_button.first.click()

            found = True

            break

    if not found:
        print("No local three-dot button found")

    else:

        print("Menu clicked successfully!")

        page.wait_for_timeout(1000)

        print("\nPress ENTER to close...")

    input()
