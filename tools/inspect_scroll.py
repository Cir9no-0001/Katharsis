"""
File Name: inspect_scroll.py
Author: Stanley Chen
Date Created: August 31, 2026
Description: 
    Connects to an existing Chrome browser session using Playwright's
    Chrome DevTools Protocol (CDP) connection and finds scrollable containers 
    in the current page.

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


# MAIN
with sync_playwright() as p:
    # Connects to an already-running Chrome instance to avoid storing credentials or session cookies
    browser = connect_browser(p)
    page = browser.contexts[0].pages[0]

    # Search for scrollable containers and return container metadata
    print("Searching for scrollable containers...\n")

    results = page.evaluate("""
    () => {

        const elements = document.querySelectorAll("*");
        let found = [];

        for (const [index, e] of elements.entries()) {
            const style = getComputedStyle(e);
            const difference = e.scrollHeight - e.clientHeight;

            if (
                difference > 300 &&
                (style.overflowY === "auto" ||
                style.overflowY === "scroll")
            ) {
                found.push({
                    index: index,
                    tag: e.tagName,
                    class: typeof e.className === "string"
                        ? e.className.slice(0,200)
                        : "",
                    id: e.id,
                    scrollHeight: e.scrollHeight,
                    clientHeight: e.clientHeight,
                    difference: difference,
                    overflowY: style.overflowY
                });

            }
        }

        return found;
    }
    """)

    print(
        f"Found {len(results)} possible scroll containers\n"
    )

    for item in results:
        print("INDEX:", item["index"])
        print("TAG:", item["tag"])
        print("CLASS:", item["class"])
        print("ID:", item["id"])
        print("scrollHeight:", item["scrollHeight"])
        print("clientHeight:", item["clientHeight"])
        print("difference:", item["difference"])
        print("overflow:", item["overflowY"])

    input("\nPress ENTER...")
