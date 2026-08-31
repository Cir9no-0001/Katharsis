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

DELETE_MODE = True
MAX_DELETE = 10


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

"""
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
"""

# ==========================
# SCAN CURRENT MESSAGES
# ==========================


def is_unavailable_content(message):

    try:
        text = message.inner_text().strip()

    except:
        return False

    return (
        "Message unavailable" in text
        or
        "This content may have been deleted by its owner" in text
        or
        "hidden by their privacy settings" in text
    )


def scan_messages(page):

    deleted_count = 0

    while True:
        if deleted_count >= MAX_DELETE:
            print("Delete limit reached")
            break

        message_list = get_messages(page)

        if not message_list:
            print("No messages found")
            break

        deleted_this_round = False

        for i, message in enumerate(message_list):
            try:
                text = message.inner_text().strip()

            except:
                text = "[MEDIA]"

            if not text:
                text = "[MEDIA]"

            print("\n======================")
            print(f"{i}: {text[:80]}")

            if unsend_message(page, message):
                deleted_count += 1
                print(f"Deleted: {deleted_count}/{MAX_DELETE}")

                deleted_this_round = True

                break

            else:
                print("Not deletable")

        if not deleted_this_round:
            print("No more deletable messages visible")
            break

        page.wait_for_timeout(1000)


def get_messages(page):

    result = []

    text_messages = page.locator("div[dir='auto']")

    for i in range(text_messages.count()):
        msg = text_messages.nth(i)

        if msg.inner_text().strip():
            result.append(msg)

    media_messages = page.locator("img.x1iyjqo2.x193iq5w.xl1xv1r")

    for i in range(media_messages.count()):
        result.append(media_messages.nth(i))

    unavailable_messages = page.locator("span[dir='auto']")

    for i in range(unavailable_messages.count()):
        msg = unavailable_messages.nth(i)

        if is_unavailable_content(msg):
            parent = msg

            for _ in range(5):
                parent = parent.locator("..")

            result.append(parent)

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
