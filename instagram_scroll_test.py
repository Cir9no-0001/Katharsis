"""
File Name: inspect_scroll_test.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and identifies Instagram's
    dynamic message scroll container to test message loading.
    
"""

# CONFIGURATION
from pathlib import Path
from playwright.sync_api import sync_playwright


# Path to Chrome's dynamically generated DevTools endpoint
DEVTOOLS_FILE = Path.home() / "AppData/Local/Google/Chrome/User Data/DevToolsActivePort"


# Connect to an existing Chrome session through CDP
def connect_browser(playwright):
    lines = DEVTOOLS_FILE.read_text().splitlines()
    ws = (f"ws://127.0.0.1:{lines[0]}{lines[1]}")
    return playwright.chromium.connect_over_cdp(ws)


# Finds the correct IG scroll container (Avoids relying on DOM indexes because IG dynamically rebuilds elements)
def get_scroll_container(page):
    return page.evaluate_handle("""
    () => {
        const elements = [
            ...document.querySelectorAll("*")
        ];

        return elements.find(e => {
            const style = getComputedStyle(e);
            return (
                style.overflowY === "scroll" &&
                e.scrollHeight > e.clientHeight
            );
        });
    }
    """)


# MAIN
with sync_playwright() as p:
    # Connects to an already-running Chrome instance to avoid storing credentials or session cookies
    browser = connect_browser(p)
    page = browser.contexts[0].pages[0]

    print("URL:", page.url)
    print("\nBefore scroll:")
    messages = page.locator("div[dir='auto']")
    print("Messages:", messages.count())
    print("\nFinding scroll container...")

    # Scroll if correct scrollable container exists and returns message count after
    scroll_box = get_scroll_container(page)

    if scroll_box:
        print("Scroll container found")
        print("Before:", scroll_box.evaluate(
            "(e)=>({top:e.scrollTop,height:e.scrollHeight})"))
        print("\nScrolling up...")

        scroll_box.evaluate("(e)=>e.scrollBy(0,-500)")

        page.wait_for_timeout(3000)

        print("After:", scroll_box.evaluate(
            "(e)=>({top:e.scrollTop,height:e.scrollHeight})"))

    else:
        print("Scroll container not found")

    print("\nAfter scroll:")
    messages = page.locator("div[dir='auto']")
    print("Messages:", messages.count())
    input("\nPress ENTER to close...")
