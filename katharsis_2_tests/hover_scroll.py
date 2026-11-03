"""
File Name: hover_scroll.py
Author: Stanley Chen
Version: 0.1.0
Description:
    Continuously highlights the lowest visible Instagram message,
    waits 2 seconds, scrolls upward by approximately one message
    height plus a fixed buffer, and repeats.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright


# Configuration
DEVTOOLS_FILE = (
    Path.home()
    / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"
)

WAIT_TIME_MS = 2000
SCROLL_BUFFER_PX = 24

CONTENT_SELECTOR = (
    'div[dir="auto"], '
    'img.x1iyjqo2.x193iq5w.xl1xv1r'
)


def connect_browser():
    """Connect to the existing authenticated Chrome session."""

    port, browser_path = DEVTOOLS_FILE.read_text().splitlines()[:2]

    playwright = sync_playwright().start()

    browser = playwright.chromium.connect_over_cdp(
        f"ws://127.0.0.1:{port}{browser_path}"
    )

    context = browser.contexts[0]
    page = context.pages[0]

    page.bring_to_front()

    print(f"Connected: {page.url}")

    return playwright, page


def get_messages(page):
    return page.evaluate(
        """
        (contentSelector) => {
            document.querySelectorAll(
                '[data-katharsis-hover-scroll]'
            ).forEach(el => {
                el.removeAttribute('data-katharsis-hover-scroll');
            });

            const content = document.querySelectorAll(contentSelector);
            const wrappers = new Set();

            for (const element of content) {
                let node = element;

                for (let i = 0; i < 15 && node; i++) {
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

            const messages = Array.from(wrappers).filter(el => {
                const rect = el.getBoundingClientRect();

                return (
                    rect.height > 0 &&
                    rect.top < window.innerHeight &&
                    rect.bottom > 0
                );
            });

            messages.forEach((message, index) => {
                message.setAttribute(
                    'data-katharsis-hover-scroll',
                    String(index)
                );
            });

            return messages.map((message, index) => ({
                id: index,
                height: message.getBoundingClientRect().height
            }));
        }
        """,
        CONTENT_SELECTOR
    )


def get_latest_message(page):
    messages = get_messages(page)

    if not messages:
        return None

    return messages[-1]


def highlight_message(page, message):
    target = page.locator(
        f'[data-katharsis-hover-scroll="{message["id"]}"]'
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

    print(
        f"Highlighted message | "
        f"Height: {message['height']:.1f}px"
    )


def scroll_up(page, message):
    """Scroll upwards by message height plus buffer."""

    distance = message["height"] + SCROLL_BUFFER_PX

    result = page.evaluate(
        """
        (distance) => {
            const target = document.querySelector(
                '[data-katharsis-hover-scroll]'
            );

            if (!target) return null;

            // Find the nearest vertically scrollable ancestor.
            let container = target.parentElement;

            while (container && container !== document.body) {
                const style = getComputedStyle(container);

                if (
                    /auto|scroll/.test(style.overflowY) &&
                    container.scrollHeight > container.clientHeight + 2
                ) {
                    const before = container.scrollTop;

                    container.scrollTop = before - distance;

                    return {
                        before: before,
                        after: container.scrollTop,
                        height: container.scrollHeight,
                        distance: distance
                    };
                }

                container = container.parentElement;
            }

            return null;
        }
        """,
        distance
    )

    if result is None:
        print("ERROR: No scrollable ancestor found.")
        return

    print(
        f"Scroll distance: {result['distance']:.1f}px | "
        f"Before: {result['before']:.1f}px | "
        f"After: {result['after']:.1f}px"
    )

    if result["before"] == result["after"]:
        print("WARNING: Scroll position did not change.")


def main():
    playwright, page = connect_browser()

    try:
        while True:
            message = get_latest_message(page)

            if message is None:
                print("No visible messages found.")
                page.wait_for_timeout(WAIT_TIME_MS)
                continue

            highlight_message(page, message)

            # Allow time to inspect the highlighted message.
            page.wait_for_timeout(WAIT_TIME_MS)

            scroll_up(page, message)

            # Allow Instagram to render newly exposed messages.
            page.wait_for_timeout(WAIT_TIME_MS)

    except KeyboardInterrupt:
        print("\nStopping hover_scroll.")

    finally:
        playwright.stop()


if __name__ == "__main__":
    main()
