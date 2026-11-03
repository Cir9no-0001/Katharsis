"""
File Name: katharsis.py
Author: Stanley Chen
Version: 1.1.2
Date Created: August 31, 2026
Description:
    Automates Instagram message scanning and removal using Playwright.
    Detects owned messages, optionally unsends messages, and scrolls through
    message history to process older conversations.

Sections:
    CONFIGURATION
    CONNECT TO CHROME
    SCAN CURRENT MESSAGES
    MESSAGE UNSENDING
    SCROLL MESSAGE HISTORY
    EXECUTION
"""

# ==========================
# CONFIGURATION
# ==========================

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

DEVTOOLS_FILE = (
    Path.home()
    / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"
)

load_dotenv()
USERNAME = os.getenv("INSTAGRAM_USERNAME")

DELETE_MODE = True
MAX_DELETE = 100
SCROLL_BUFFER_PX = 24
DOM_REFRESH_WAIT_MS = 4000

MESSAGE_CONTENT_SELECTOR = (
    'div[dir="auto"], '
    'img.x1iyjqo2.x193iq5w.xl1xv1r'
)
MESSAGE_MARKER = "data-katharsis-scroll"


# ==========================
# CONNECT TO CHROME
# ==========================

def connect_browser(playwright):
    """Connect to the existing Chrome session through its DevTools port."""

    lines = DEVTOOLS_FILE.read_text(encoding="utf-8").splitlines()

    if len(lines) < 2:
        raise RuntimeError(
            f"Unexpected DevToolsActivePort contents: {DEVTOOLS_FILE}"
        )

    port, browser_path = lines[:2]
    ws_endpoint = f"ws://127.0.0.1:{port}{browser_path}"

    return playwright.chromium.connect_over_cdp(ws_endpoint)


# ==========================
# SCAN CURRENT MESSAGES
# ==========================

def is_unavailable_content(message):
    """Return True when a message contains Instagram's unavailable text."""

    try:
        text = message.inner_text().strip()
    except Exception:
        return False

    unavailable_phrases = (
        "Message unavailable",
        "This content may have been deleted by its owner",
        "hidden by their privacy settings",
    )

    return any(phrase in text for phrase in unavailable_phrases)


def create_message_signature(message):
    """Create a basic signature for checking whether the bottom message changed."""

    box = message.bounding_box()

    if not box:
        return None

    try:
        text = message.inner_text().strip()
    except Exception:
        text = ""

    if is_unavailable_content(message):
        content_type = "UNAVAILABLE"
    elif text:
        content_type = "TEXT"
    else:
        content_type = "MEDIA"

    side = "LEFT" if box["x"] < 1200 else "RIGHT"

    return (
        content_type,
        text[:50],
        round(box["width"]),
        round(box["height"]),
        side,
    )


def get_messages(page):
    """Return visible message-wrapper locators ordered from top to bottom.

    This ports the sibling-based wrapper detection from hover_scroll.py.
    Each call rebuilds the marker attributes, so locators from an earlier
    call must not be reused after calling get_messages() again.
    """

    message_ids = page.evaluate(
        """
        ({contentSelector, markerName}) => {

            // Remove markers from the previous scan.
            document.querySelectorAll(`[${markerName}]`).forEach(el => {
                el.removeAttribute(markerName);
            });

            const content = document.querySelectorAll(contentSelector);
            const wrappers = new Set();

            // Find the nearest ancestor that is one of multiple message siblings.
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

                    if (siblings.length >= 2 && siblings.includes(node)) {
                        wrappers.add(node);
                        break;
                    }

                    node = parent;
                }
            }

            // Preserve Katharsis's fallback for unavailable-message notices.
            const unavailablePhrases = [
                'Message unavailable',
                'This content may have been deleted by its owner',
                'hidden by their privacy settings'
            ];

            for (const span of document.querySelectorAll('span[dir="auto"]')) {
                const text = (span.innerText || '').trim();

                if (!unavailablePhrases.some(phrase => text.includes(phrase))) {
                    continue;
                }

                let wrapper = span;

                for (let i = 0; i < 5 && wrapper; i++) {
                    wrapper = wrapper.parentElement;
                }

                if (wrapper) wrappers.add(wrapper);
            }

            // Keep visible messages and order them top-to-bottom.
            const messages = Array.from(wrappers).filter(el => {
                const rect = el.getBoundingClientRect();

                return (
                    rect.height > 0 &&
                    rect.top < window.innerHeight &&
                    rect.bottom > 0
                );
            });

            messages.sort((a, b) => {
                const position = a.compareDocumentPosition(b);

                if (position & Node.DOCUMENT_POSITION_FOLLOWING) return -1;
                if (position & Node.DOCUMENT_POSITION_PRECEDING) return 1;
                return 0;
            });

            messages.forEach((message, index) => {
                message.setAttribute(markerName, String(index));
            });

            return messages.map((_, index) => index);
        }
        """,
        {
            "contentSelector": MESSAGE_CONTENT_SELECTOR,
            "markerName": MESSAGE_MARKER,
        },
    )

    return [
        page.locator(f'[{MESSAGE_MARKER}="{message_id}"]')
        for message_id in message_ids
    ]


def scan_messages(page):
    """Scan the lowest visible message, unsend it if eligible, or scroll past it."""

    deleted_count = 0

    while True:
        if DELETE_MODE and deleted_count >= MAX_DELETE:
            print("Delete limit reached")
            break

        # Re-detect messages after every deletion or scroll.
        messages = get_messages(page)

        if not messages:
            print("No messages visible")
            break

        # get_messages() returns message wrappers in document order.
        target = messages[-1]

        target.evaluate(
            """
            element => {
                element.style.outline = "3px solid red";
                element.style.backgroundColor = "rgba(255, 0, 0, 0.15)";
            }
            """
        )

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
                round(box["height"]),
            )
        )

        try:
            text = target.inner_text().strip()
        except Exception:
            text = ""

        if is_unavailable_content(target):
            print("[UNAVAILABLE]")
        elif text:
            print(text[:80])
        else:
            print("[MEDIA]")

        # Attempt deletion before moving farther into message history.
        if DELETE_MODE and unsend_message(page, target):
            deleted_count += 1
            print(f"Deleted {deleted_count}/{MAX_DELETE}")
            page.wait_for_timeout(1000)
            continue

        print("Not deletable, scrolling")

        # Use the height of Katharsis's detected message wrapper.
        # This is the same distance calculation used by hover_scroll.py.
        if not scroll_message(page, target, box["height"]):
            print("Scroll failed or reached the top of the conversation.")
            return

        # Instagram loads and reflows older messages asynchronously.
        # The next loop iteration re-runs get_messages() after this wait.
        print(
            f"Waiting {DOM_REFRESH_WAIT_MS}ms for message history to refresh...")
        page.wait_for_timeout(DOM_REFRESH_WAIT_MS)


# ==========================
# MESSAGE UNSENDING
# ==========================

def unsend_message(page, message):
    """Open the selected message's menu and invoke Instagram's Unsend action."""

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

            unsend = page.get_by_role("button", name="Unsend")

            if not unsend.count():
                print("Menu opened but Unsend missing")
                page.keyboard.press("Escape")
                return False

            print("Clicking Unsend")
            unsend.first.click()
            page.wait_for_timeout(700)

            confirm = page.get_by_role("button", name="Unsend")

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

def scroll_message(page, message, message_height):
    """Scroll upward by the detected message height plus the fixed buffer."""

    message_id = message.get_attribute(MESSAGE_MARKER)

    if message_id is None:
        print("ERROR: Selected message has no Katharsis marker.")
        return False

    distance = float(message_height) + SCROLL_BUFFER_PX

    result = page.evaluate(
        """
        ({distance, messageId}) => {
            const target = document.querySelector(
                `[data-katharsis-scroll="${messageId}"]`
            );

            if (!target) return null;

            // Match hover_scroll.py: find the nearest scrollable ancestor.
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
                        scrollHeight: container.scrollHeight,
                        clientHeight: container.clientHeight,
                        distance: distance
                    };
                }

                container = container.parentElement;
            }

            return null;
        }
        """,
        {
            "distance": distance,
            "messageId": message_id,
        },
    )

    if result is None:
        print("ERROR: No scrollable ancestor found for selected message.")
        return False

    print(
        f"Scroll distance: {result['distance']:.1f}px "
        f"(message: {message_height:.1f}px + buffer: {SCROLL_BUFFER_PX}px) | "
        f"Before: {result['before']:.1f}px | "
        f"After: {result['after']:.1f}px"
    )

    if abs(result["before"] - result["after"]) < 0.5:
        print("WARNING: Scroll position did not change.")
        return False

    return True


# ==========================
# EXECUTION
# ==========================

def main():
    with sync_playwright() as playwright:
        print("Connecting to Chrome...")

        browser = connect_browser(playwright)
        context = browser.contexts[0]

        if not context.pages:
            raise RuntimeError("No Chrome pages are available.")

        page = context.pages[0]
        page.bring_to_front()

        print("Current page:", page.url)

        scan_messages(page)

        print("\nScan complete")
        input("\nPress ENTER to close...")


if __name__ == "__main__":
    main()
