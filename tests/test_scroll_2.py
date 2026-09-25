from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"

load_dotenv()
USERNAME = os.getenv("INSTAGRAM_USERNAME")

HIGHLIGHT_DELAY = 2000
SCROLL_DELAY = 1500


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


def highlight_message(message):
    message.evaluate("""
        element => {
            element.style.outline = "4px solid red";
            element.style.outlineOffset = "2px";
            element.style.backgroundColor = "rgba(255, 0, 0, 0.15)";
        }
    """)


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
                after: target.scrollTop,
                moved: before - target.scrollTop,
                scrollHeight: target.scrollHeight,
                clientHeight: target.clientHeight
            };
        }
        """,
        amount
    )

    print("Scrolled:", amount, result)

    return result


def main():
    with sync_playwright() as p:
        print("Connecting to Chrome...")

        browser = connect_browser(p)

        page = browser.contexts[0].pages[0]

        print("Current page:", page.url)

        while True:
            messages = get_messages(page)

            if not messages:
                print("No messages found")
                break

            # Select the same newest message used by Katharsis.
            message = messages[-1]

            box = message.bounding_box()

            if not box:
                print("Could not measure message")
                continue

            height = box["height"]

            try:
                text = message.inner_text().strip()
            except:
                text = ""

            # Highlight the exact element whose height we are measuring.
            highlight_message(message)

            print("\n================")
            print("SELECTED MESSAGE")
            print("================")
            print("Message:", text[:200] if text else "[NO TEXT]")
            print(f"Width:  {box['width']:.1f}px")
            print(f"Height: {height:.1f}px")
            print(f"Scroll: {height:.1f}px")
            print("================")

            # Give you time to see exactly what was measured.
            page.wait_for_timeout(HIGHLIGHT_DELAY)

            # Use the OLD scrolling mechanism.
            scroll_message(page, height)

            page.wait_for_timeout(SCROLL_DELAY)


if __name__ == "__main__":
    main()
