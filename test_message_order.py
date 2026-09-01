"""
File Name: test_message_order.py
Author: Stanley Chen
Date Created: August 31, 2026
Description:
    Debug script to identify Instagram DM message containers
    and determine their true DOM ordering.
"""


from pathlib import Path
from playwright.sync_api import sync_playwright

DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"


def connect_browser(playwright):

    lines = DEVTOOLS_FILE.read_text().splitlines()

    ws_endpoint = (
        f"ws://127.0.0.1:{lines[0]}"
        f"{lines[1]}"
    )

    browser = playwright.chromium.connect_over_cdp(ws_endpoint)

    return browser


def find_message_container(element):

    current = element

    for level in range(15):

        current = current.locator("..")

        try:
            text = current.inner_text().strip()

        except:
            continue

        images = current.locator("img").count()

        if text or images:

            return current, level + 1

    return None, None


def scan_messages(page):
    candidates = page.locator(
        "div[dir='auto'], img.x1iyjqo2.x193iq5w.xl1xv1r"
    )

    print(
        "Candidates found:",
        candidates.count()
    )

    seen = []

    for i in range(candidates.count()):

        element = candidates.nth(i)

        container, level = find_message_container(element)

        if container:
            found = False

            for old in seen:

                if container == old:
                    found = True

            if not found:

                seen.append(container)

                try:
                    text = container.inner_text().strip()

                except:
                    text = ""

                print("\n================")
                print(
                    "MESSAGE:",
                    len(seen)
                )

                print(
                    "Parent level:",
                    level
                )

                box = container.bounding_box()

                print(
                    "POSITION:",
                    box
                )

                if text:
                    print(
                        text[:100]
                    )

                else:
                    print(
                        "[MEDIA]"
                    )


def main():

    with sync_playwright() as p:

        print("Connecting to Chrome...")

        browser = connect_browser(p)

        page = browser.contexts[0].pages[0]

        print(
            "Current page:",
            page.url
        )

        scan_messages(page)

        input(
            "\nPress ENTER to close..."
        )


if __name__ == "__main__":
    main()
