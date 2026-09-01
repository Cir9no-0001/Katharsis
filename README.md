# Katharsis

# Katharsis

<p align="center">

  <img src="katharsis.png" width="100%">

</p>

**Status:** Active Development

![Version](https://img.shields.io/badge/version-v1.1.0-blue)

![Python](https://img.shields.io/badge/python-3.12-blue)

![Playwright](https://img.shields.io/badge/automation-Playwright-green)

> A Playwright-based browser automation tool for scanning, detecting, and managing Instagram messages through an existing Chrome session using the Chrome DevTools Protocol (CDP).

Last updated: 2026-08-31

---

# Project Overview

## What is this?

Katharsis is a Python browser automation project that connects to an existing Chrome session through the Chrome DevTools Protocol (CDP) and automates Instagram message management workflows.

The project explores how modern JavaScript-based applications dynamically render content, expose interactive controls, and handle user actions through browser automation.

Currently, Katharsis focuses on identifying messages, determining available actions, and safely automating message removal through Playwright.

Katharsis currently supports:

- Connecting to an existing Chrome browser session through CDP
- Inspecting dynamically generated DOM structures
- Detecting text, media, and unavailable message types
- Identifying user-owned messages through available browser actions
- Automating Instagram message unsending workflows
- Navigating dynamically loaded message history
- Testing reliable automation strategies against changing web interfaces

## Tech Stack

- **Language:** Python 3.12
- **Browser Automation:** Playwright
- **Browser Integration:** Chrome DevTools Protocol (CDP)
- **Environment Management:** python-dotenv
- **Version Control:** Git

## Key Features

### Chrome Session Integration

- Connects directly to an already-running Chrome instance through CDP
- Uses the user's existing authenticated browser session
- Avoids storing passwords, cookies, or authentication tokens
- Allows automation without rebuilding login workflows

### Dynamic Message Detection

- Identifies visible Instagram message elements
- Supports multiple message types:
  - Text messages
  - Media messages
  - Unavailable/deleted content messages
- Extracts message metadata for analysis and tracking
- Handles dynamically generated page structures

### Message Ownership Detection

- Determines whether messages belong to the authenticated user
- Uses Instagram's available message actions instead of manually parsing sender information
- Prevents attempting unsupported actions on other users' messages

### Automated Message Removal

- Locates available message controls
- Opens message action menus
- Executes unsend workflows
- Supports configurable deletion limits for safer testing

### Dynamic History Navigation

- Detects scrollable message containers automatically
- Navigates through older conversation history
- Handles dynamically loaded content while scanning messages
- Uses message signatures to verify movement through history

## Why was this built?

Real story? I wanted to automate mass unsending messages on Instagram without relying on sketchy extensions that wanted my cookies.

Modern web applications are heavily dependent on JavaScript rendering, dynamic content loading, and frequently changing DOM structures. Traditional automation methods often fail because elements may not exist until runtime or may be recreated during interaction.

Katharsis was created to explore browser automation at a deeper level by understanding:

- How browsers expose automation interfaces through CDP
- How dynamic web applications structure and render content
- How Playwright interacts with complex user interfaces
- How reliable automation workflows can be designed around unstable DOM environments
- How destructive automation tasks can be performed safely

The project serves as a foundation for experimenting with browser automation, DOM analysis, and future automation tooling.

---

## License

This project is source-available but **not open source**. Copyright (c)
2026 Stanley Chen - All Rights Reserved.

You may clone, fork, and run this project locally for personal, non-commercial
evaluation, testing, and code review. Commercial use, redistribution,
hosting as a service, and incorporation into other projects are not
permitted. See [LICENSE](LICENSE) for the full terms.
