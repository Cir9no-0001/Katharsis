"""
gpt testing shit
    
"""


from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"

load_dotenv()
USERNAME = os.getenv("INSTAGRAM_USERNAME")


def connect_browser(playwright):
    lines = DEVTOOLS_FILE.read_text().splitlines()
    port = lines[0]
    browser_path = lines[1]
    ws_endpoint = f"ws://127.0.0.1:{port}{browser_path}"
    return playwright.chromium.connect_over_cdp(ws_endpoint)


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

    candidates = page.locator(
        "div[dir='auto'], img.x1iyjqo2.x193iq5w.xl1xv1r"
    )

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

    return result


def main():
    with sync_playwright() as p:
        print("Connecting to Chrome...")

        browser = connect_browser(p)
        page = browser.contexts[0].pages[0]

        print("Current page:", page.url)

        messages = get_messages(page)

        if not messages:
            print("No messages found.")
            input("Press ENTER to close...")
            return

        # Same newest-message selection used by Katharsis
        message = messages[-1]

        box = message.bounding_box()

        if not box:
            print("Could not get bounding box.")
            input("Press ENTER to close...")
            return

        height = box["height"]

        try:
            text = message.inner_text().strip()
        except:
            text = ""

        # Highlight the EXACT element being measured
        message.evaluate("""
            element => {
                element.style.outline = '4px solid red';
                element.style.outlineOffset = '2px';
                element.style.backgroundColor = 'rgba(255, 0, 0, 0.15)';
            }
        """)

        print("\n================")
        print("NEWEST MESSAGE")
        print("================")
        print("Message:", text[:200] if text else "[NO TEXT]")
        print(f"X:      {box['x']:.1f}")
        print(f"Y:      {box['y']:.1f}")
        print(f"Width:  {box['width']:.1f}px")
        print(f"Height: {height:.1f}px")
        print("================")
        print("\nThe element being measured is highlighted RED in Chrome.")
        print("Leave Chrome open so you can inspect it.")

        input("\nPress ENTER to close...")


if __name__ == "__main__":
    main()
