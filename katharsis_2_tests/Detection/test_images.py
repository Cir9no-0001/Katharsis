
"""
File Name: test_images.py
Author: Stanley Chen
Version: 0.1.0
Description:
    Detects the most recent visible Instagram image or Reel message,
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

CONTENT_SELECTOR = "img"


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


# Detect media messages

def get_messages(page):
    """Find visible image-containing message containers."""

    return page.evaluate(
        """
        ({contentSelector, maxAncestors}) => {

            document.querySelectorAll(
                '[data-katharsis-test-media]'
            ).forEach(el => {
                el.removeAttribute('data-katharsis-test-media');
            });

            const content = document.querySelectorAll(contentSelector);
            const wrappers = new Set();

            for (const element of content) {
                const imageRect = element.getBoundingClientRect();

                // Ignore invisible or unloaded images.
                if (
                    imageRect.width === 0 ||
                    imageRect.height === 0 ||
                    imageRect.bottom <= 0 ||
                    imageRect.top >= window.innerHeight
                ) {
                    continue;
                }

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
                    rect.width > 0 &&
                    rect.height > 0 &&
                    rect.top < window.innerHeight &&
                    rect.bottom > 0 &&
                    message.querySelector(contentSelector)
                );
            });

            return messages.map((message, index) => {
                const rect = message.getBoundingClientRect();

                message.setAttribute(
                    'data-katharsis-test-media',
                    String(index)
                );

                const images = Array.from(
                    message.querySelectorAll('img')
                ).map(img => {
                    const imageRect = img.getBoundingClientRect();

                    return {
                        alt: img.alt,
                        src: img.currentSrc || img.src,
                        className: img.className,
                        width: imageRect.width,
                        height: imageRect.height,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        complete: img.complete
                    };
                });

                return {
                    id: index,
                    tag: message.tagName,
                    className: message.className,
                    content: message.innerText.trim(),

                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,

                    imageCount: images.length,
                    svgCount: message.querySelectorAll('svg').length,

                    images: images
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
    """Hover over and highlight the most recent media message."""

    target = page.locator(
        f'[data-katharsis-test-media="{message["id"]}"]'
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
    """Print metadata for the selected media message."""

    print("\\n" + "=" * 50)
    print(f"Message ID:   {message['id']}")
    print(f"Element:      {message['tag']}")
    print(f"Class:        {message['className']}")
    print(f"Position:     ({message['x']:.1f}, {message['y']:.1f})")
    print(
        f"Dimensions:   "
        f"{message['width']:.1f} x {message['height']:.1f}"
    )
    print(f"Images:       {message['imageCount']}")
    print(f"SVGs:         {message['svgCount']}")
    print(f"Content:      {message['content']}")

    for index, img in enumerate(message["images"]):
        print(f"\\nImage {index + 1}:")
        print(f"  Alt:          {img['alt']}")
        print(f"  Source:       {img['src']}")
        print(f"  Class:        {img['className']}")
        print(
            f"  Dimensions:   "
            f"{img['width']:.1f} x {img['height']:.1f}"
        )
        print(
            f"  Natural size: "
            f"{img['naturalWidth']} x {img['naturalHeight']}"
        )
        print(f"  Loaded:       {img['complete']}")


# Execution

def main():
    with sync_playwright() as playwright:
        page = connect_browser(playwright)

        messages = get_messages(page)

        if not messages:
            print("No visible media messages found.")
            return

        message = messages[-1]

        highlight_message(page, message)
        print_metadata(message)

        input("\\nPress ENTER to close the test...")


if __name__ == "__main__":
    main()
