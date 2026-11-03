
"""
File Name: test_text.py
Author: Stanley Chen
Version: 0.1.0
Description:
    Detects the most recent visible Instagram text message,
    hovers over it, highlights it, and prints its metadata.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright


# Configuration

DEVTOOLS_FILE = (
    Path.home()
    / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"
)

MAX_ANCESTORS = 15

CONTENT_SELECTOR = (
    'div[dir="auto"], '
    'img.x1iyjqo2.x193iq5w.xl1xv1r'
)


# Connect to Chrome

def connect_browser(playwright):
    """Connect to the existing authenticated Chrome session."""

    port, browser_path = DEVTOOLS_FILE.read_text().splitlines()[:2]

    browser = playwright.chromium.connect_over_cdp(
        f"ws://127.0.0.1:{port}{browser_path}"
    )

    page = browser.contexts[0].pages[0]
    page.bring_to_front()

    print(f"Connected: {page.url}")

    return page


# Detect messages

def get_messages(page):
    """Find visible message containers and return their metadata."""

    return page.evaluate(
        """
        ({contentSelector, maxAncestors}) => {

            const content = document.querySelectorAll(contentSelector);
            const wrappers = new Set();

            for (const element of content) {
                let node = element;

                for (let i = 0; i < maxAncestors && node; i++) {
                    const parent = node.parentElement;

                    if (!parent) break;

                    const siblings = Array.from(parent.children).filter(
                        child =>
                            child.matches(contentSelector) ||
                            child.querySelector(contentSelector)
                    );

                    if (
                        siblings.length >= 2 &&
                        siblings.includes(node)
                    ) {
                        wrappers.add(node);
                        break;
                    }

                    node = parent;
                }
            }

            const messages = Array.from(wrappers).filter(message => {
                const rect = message.getBoundingClientRect();

                return (
                    rect.height > 0 &&
                    rect.top < window.innerHeight &&
                    rect.bottom > 0 &&
                    message.innerText.trim().length > 0
                );
            });

            messages.forEach((message, index) => {
                message.setAttribute(
                    'data-katharsis-test-text',
                    String(index)
                );
            });

            return messages.map((message, index) => {
                const rect = message.getBoundingClientRect();

                return {
                    id: index,
                    tag: message.tagName,
                    className: message.className,
                    content: message.innerText.trim(),
                    textLength: message.innerText.trim().length,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    top: rect.top,
                    bottom: rect.bottom,
                    scrollHeight: message.scrollHeight,
                    clientHeight: message.clientHeight,
                    childCount: message.children.length,
                    imageCount: message.querySelectorAll('img').length,
                    videoCount: message.querySelectorAll('video').length,
                    svgCount: message.querySelectorAll('svg').length
                };
            });
        }
        """,
        {
            "contentSelector": CONTENT_SELECTOR,
            "maxAncestors": MAX_ANCESTORS
        }
    )


# Hover and highlight

def highlight_message(page, message):
    """Hover over and highlight the most recent message."""

    target = page.locator(
        f'[data-katharsis-test-text="{message["id"]}"]'
    )

    target.hover()

    target.evaluate(
        """
        el => {
            el.style.outline = '2px solid red';
            el.style.outlineOffset = '2px';
        }
        """
    )

    print(f"Highlighted message {message['id']}")


# Display metadata

def print_metadata(message):
    """Print metadata for the selected message."""

    print("\n" + "=" * 50)
    print(f"Message ID:    {message['id']}")
    print(f"Element:       {message['tag']}")
    print(f"Class:         {message['className']}")
    print(f"Position:      ({message['x']:.1f}, {message['y']:.1f})")
    print(
        f"Dimensions:    "
        f"{message['width']:.1f} x {message['height']:.1f}"
    )
    print(f"Top / Bottom:  {message['top']:.1f} / {message['bottom']:.1f}")
    print(f"Text length:   {message['textLength']}")
    print(f"Child count:   {message['childCount']}")
    print(f"Images:        {message['imageCount']}")
    print(f"Videos:        {message['videoCount']}")
    print(f"SVGs:          {message['svgCount']}")
    print(f"Scroll height: {message['scrollHeight']}")
    print(f"Client height: {message['clientHeight']}")
    print(f"Content:       {message['content']}")


# Execution

def main():
    with sync_playwright() as playwright:
        page = connect_browser(playwright)

        messages = get_messages(page)

        if not messages:
            print("No visible messages found.")
            return

        message = messages[-1]

        highlight_message(page, message)
        print_metadata(message)

        input("\nPress ENTER to close the test...")


if __name__ == "__main__":
    main()
