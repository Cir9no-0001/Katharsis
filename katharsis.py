"""
File Name: katharsis.py
Author: Stanley Chen
Version: 1.0.0
Date Created: August 31, 2026
Description: 
    Automates Instagram message scanning and removal using Playwright.
    Detects owned messages, optionally unsends messages, and scrolls through
    message history to process older conversations.

NOTE: IT WONT RUN PROPERLY UNTIL U CHANGE DELETE_MODE AND MAX_DELETE in # CONFIGURATION
    

Sections:
    # CONFIGURATION
    # CONNECT TO CHROME
    # MESSAGE OWNERSHIP DETECTOR
    # SCAN CURRENT MESSAGES
    # MESSAGE UNSENDING
    # SCROLL MESSAGE HISTORY
    # EXECUTION
    
"""

# ==========================
# CONFIGURATION
# ==========================

from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"

load_dotenv()
USERNAME = os.getenv(
    "INSTAGRAM_USERNAME"
)

DELETE_MODE = False
MAX_DELETE = 0


# ==========================
# CONNECT TO CHROME
# ==========================

def connect_browser(playwright):
    lines = DEVTOOLS_FILE.read_text().splitlines()
    port = lines[0]
    browser_path = lines[1]
    ws_endpoint = (f"ws://127.0.0.1:{port}{browser_path}")
    browser = playwright.chromium.connect_over_cdp(ws_endpoint)

    return browser


# ==========================
# MESSAGE OWNERSHIP DETECTOR
# ==========================

def check_if_my_message(page, message):

    message.hover()
    page.wait_for_timeout(700)
    parent = message

    # Walk UPWARDS the matching menu is found
    for level in range(10):
        parent = parent.locator("..")
        options_button = parent.locator(
            f"svg[aria-label='See more options for message from {USERNAME}']")

        if options_button.count():
            print("Found menu at parent level:", level + 1)
            options_button.first.click()
            page.wait_for_timeout(500)

            # IMPORTANT: Only owned messages will have unsend button
            unsend = page.get_by_role("button", name="Unsend")
            is_mine = unsend.count() > 0

            page.keyboard.press("Escape")

            return is_mine

    # No matching menu found
    return False


# ==========================
# SCAN CURRENT MESSAGES
# ==========================

def scan_messages(page):
    message_list = get_messages(page)

    print(
        f"\nMessages loaded: {len(message_list)}"
    )

    deleted_count = 0

    for i, message in enumerate(message_list):
        text = message.inner_text().strip()

        print("\n======================")
        print(f"{i}: {text[:80]}")

        if check_if_my_message(page, message):
            print("MY MESSAGE")
            if DELETE_MODE:
                if deleted_count >= MAX_DELETE:
                    print("Delete limit reached")
                    break

                if unsend_message(page, message):
                    deleted_count += 1
                    print(f"Deleted: {deleted_count}/{MAX_DELETE}")

        else:
            print("PERMISSION DENIED")


def get_messages(page):
    messages = page.locator("div[dir='auto']")

    result = []

    for i in range(messages.count()):
        msg = messages.nth(i)
        if msg.inner_text().strip():
            result.append(msg)

    return result


# ==========================
# MESSAGE UNSENDING
# ==========================

def unsend_message(page, message):
    message.hover()
    page.wait_for_timeout(700)
    parent = message

    for level in range(10):
        parent = parent.locator("..")
        options_button = parent.locator(
            f"svg[aria-label='See more options for message from {USERNAME}']")

        if options_button.count():
            print("Opening message menu...")

            options_button.first.click()
            page.wait_for_timeout(500)

            unsend = page.get_by_role("button", name="Unsend")

            if not unsend.count():
                print("Unsend unavailable")
                page.keyboard.press("Escape")
                return False

            print("Clicking Unsend...")

            unsend.first.click()

            page.wait_for_timeout(500)

            confirm = page.get_by_role("button", name="Unsend")

            if confirm.count():
                print("Confirming...")
                confirm.first.click()
                page.wait_for_timeout(1000)

            print("Removed")

            return True

    print("Could not locate menu")

    return False


# ==========================
# SCROLL MESSAGE HISTORY
# ==========================

def scroll_up(page):

    print("Loading older messages...")

    result = page.evaluate("""
    () => {
        const elements = [
            ...document.querySelectorAll("*")
        ];

        const target = elements.find(e => {
            const style = getComputedStyle(e);
            return (
                style.overflowY === "scroll" &&
                e.scrollHeight > e.clientHeight
            );

        });

        if (!target) {
            return null;
        }

        const before = target.scrollTop;
        target.scrollBy(0,-800);

        return {
            before: before,
            after: target.scrollTop,
            height: target.scrollHeight
        };
    }
    """)

    print(result)
    page.wait_for_timeout(2000)

# ==========================
# EXECUTION
# ==========================


def main():
    with sync_playwright() as p:
        print("Connecting to Chrome...")

        browser = connect_browser(p)
        page = browser.contexts[0].pages[0]
        print("Current page:", page.url)

        for i in range(5):
            scan_messages(page)
            scroll_up(page)

        print("\nScan complete")

        input("\nPress ENTER to close...")


if __name__ == "__main__":
    main()
