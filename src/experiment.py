"""
File Name: katharsis.py
Author: Stanley Chen
Version: 1.1.0
Date Created: August 31, 2026
Description: 
    Automates Instagram message scanning and removal using Playwright.
    Detects owned messages, optionally unsends messages, and scrolls through
    message history to process older conversations.

NOTE: IT WONT RUN PROPERLY UNTIL U CHANGE DELETE_MODE AND MAX_DELETE in # CONFIGURATION
    

Sections:
    # CONFIGURATION
    # CONNECT TO CHROME
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
MAX_DELETE = 5
SCROLL_INCREMENT = 200


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


def create_message_signature(message):
    box = message.bounding_box()

    if not box:
        return None

    try:
        text = message.inner_text().strip()
    except:
        text = ""

    if is_unavailable_content(message):
        content_type = "UNAVAILABLE"

    elif text:
        content_type = "TEXT"

    else:
        content_type = "MEDIA"

    side = (
        "LEFT"
        if box["x"] < 1200
        else
        "RIGHT"
    )

    return (
        content_type,
        text[:50],
        round(box["width"]),
        round(box["height"]),
        side
    )


def scan_messages(page):
    deleted_count = 0

    while True:
        # TO-DO: Change deletion limiter when testing over
        if deleted_count >= MAX_DELETE:
            print("Delete limit reached")
            break

        # TO-DO: Fix message detection, signature display and selection here
        messages = get_messages(page)

        if not messages:
            print("No messages visible")
            break

        target = messages[-1]
        box = target.bounding_box()

        if not box:
            print("Waiting for render...")
            page.wait_for_timeout(1000)
            continue

        print("\n================")
        print("Checking:")
        print(
            (
                round(box["x"]),
                round(box["y"]),
                round(box["width"]),
                round(box["height"])
            )
        )

        try:
            text = target.inner_text().strip()

        except:
            text = ""

        if is_unavailable_content(target):
            print("[UNAVAILABLE]")

        elif text:
            print(text[:80])

        else:
            print("[MEDIA]")

        # Delete message if ownership
        if DELETE_MODE and unsend_message(page, target):
            deleted_count += 1
            print(f"Deleted {deleted_count}/{MAX_DELETE}")

            # IMPORTANT: Increase this if laggy DOM loading
            page.wait_for_timeout(1000)

            continue

        print("Not deletable, scrolling")

        # Jump if cannot delete message/no ownership
        target_signature = create_message_signature(target)
        scroll_amount = 200

        while True:
            scroll_message(page, scroll_amount)
            page.wait_for_timeout(1500)
            messages = get_messages(page)

            if not messages:
                print("No more messages")
                return

            newest = messages[-1]
            newest_signature = create_message_signature(newest)

            print("Old:", target_signature)
            print("New:", newest_signature)

            if newest_signature != target_signature:
                print("Successfully moved past message")
                break

            print("Same message still visible, increasing scroll")

            scroll_amount += 200

            if scroll_amount > 1200:
                print("Could not move past message")
                break


def find_message_container(element):
    current = element

    for level in range(15):
        current = current.locator("..")

        try:
            text = current.inner_text().strip()
        except:
            text = ""

        images = current.locator("img").count()

        if text or images:
            return current

    return None


def get_messages(page):
    result = []
    seen = []

    # Normal text + media detection below

    # VERY IMPORTANT: THIS SHIT CHANGES AND BREAKS EVERYTHING IF IG UPDATES
    candidates = page.locator("div[dir='auto'], img.x1iyjqo2.x193iq5w.xl1xv1r")
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    for i in range(candidates.count()):
        element = candidates.nth(i)
        container = find_message_container(element)
        if container:
            duplicate = False

            for old in seen:
                if container == old:
                    duplicate = True
                    break

            if not duplicate:
                seen.append(container)
                result.append(container)

    # Unavalible message detection below

    unavailable_messages = page.locator("span[dir='auto']")

    for i in range(unavailable_messages.count()):
        msg = unavailable_messages.nth(i)
        if is_unavailable_content(msg):
            parent = msg

            for _ in range(5):
                parent = parent.locator("..")

            duplicate = False

            for old in seen:
                if parent == old:
                    duplicate = True
                    break

            if not duplicate:
                seen.append(parent)
                result.append(parent)

    return result


# ==========================
# MESSAGE UNSENDING
# ==========================

def unsend_message(page, message):

    message.hover()
    page.wait_for_timeout(700)

    parent = message

    for level in range(15):

        parent = parent.locator("..")

        options_button = parent.locator(
            f"svg[aria-label='See more options for message from {USERNAME}']"
        )

        if options_button.count():

            print("Found menu at level:", level + 1)

            options_button.first.click()
            page.wait_for_timeout(700)

            unsend = page.get_by_role(
                "button",
                name="Unsend"
            )

            if not unsend.count():

                print("Menu opened but Unsend missing")

                page.keyboard.press("Escape")

                return False

            print("Clicking Unsend")

            unsend.first.click()

            page.wait_for_timeout(700)

            confirm = page.get_by_role(
                "button",
                name="Unsend"
            )

            if confirm.count():

                print("Confirming Unsend")

                confirm.first.click()

                page.wait_for_timeout(1000)

            print("Removed")

            return True

    print("Could not find message menu")

    return False


# ==========================
# SCROLL MESSAGE HISTORY
# ==========================

def scroll_message(page, amount):

    result = page.evaluate(
        """
        (amount) => {

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

            target.scrollBy(
                0,
                -amount
            );

            return {
                before: before,
                after: target.scrollTop
            };
        }
        """,
        amount
    )

    print(
        "Scrolled:",
        amount,
        result
    )


# ==========================
# EXECUTION
# ==========================

def main():
    with sync_playwright() as p:
        print("Connecting to Chrome...")

        browser = connect_browser(p)
        page = browser.contexts[0].pages[0]
        print("Current page:", page.url)

        scan_messages(page)

        print("\nScan complete")

        input("\nPress ENTER to close...")


if __name__ == "__main__":
    main()
