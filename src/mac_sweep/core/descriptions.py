"""Application descriptions for mac-sweep.

Provides human-readable descriptions for common macOS applications.
"""

from __future__ import annotations

from typing import Any

KNOWN_APP_DESCRIPTIONS: dict[str, str] = {
    "1Password 7": "Password manager and secure vault",
    "Activity Monitor": "macOS system resource monitor",
    "Alfred": "Productivity launcher and workflow automation",
    "App Store": "Apple's app marketplace",
    "Arc": "Chromium-based web browser by The Browser Company",
    "Automator": "macOS visual workflow automation tool",
    "Books": "Apple e-book and audiobook reader",
    "Calculator": "Apple's built-in calculator",
    "Calendar": "Apple calendar and scheduling app",
    "Chess": "Apple's built-in chess game",
    "Claude": "Anthropic's AI assistant",
    "Contacts": "Apple address book and contact manager",
    "Cursor": "AI-powered code editor based on VS Code",
    "DaVinci Resolve": "Professional video editing and color grading",
    "Dictionary": "Apple's built-in dictionary and thesaurus",
    "Discord": "Voice, video, and text communication platform",
    "Disk Utility": "macOS disk management tool",
    "Docker": "Container platform for building and running apps",
    "Dropbox": "Cloud file storage and synchronization",
    "FaceTime": "Apple video and audio calling app",
    "Fantastical": "Calendar app with natural language input",
    "Figma": "Collaborative interface design tool",
    "Find My": "Apple device and item tracking",
    "Finder": "macOS file manager",
    "Firefox": "Open-source web browser by Mozilla",
    "Font Book": "macOS font management tool",
    "Freeform": "Apple collaborative whiteboard app",
    "GarageBand": "Apple music creation studio",
    "GitHub Desktop": "Git GUI client by GitHub",
    "Google Chrome": "Web browser by Google",
    "Grapher": "macOS 2D/3D equation graphing tool",
    "Handbrake": "Open-source video transcoder",
    "Home": "Apple HomeKit device control",
    "IINA": "Modern media player for macOS",
    "Image Capture": "macOS image import from cameras/scanners",
    "iMovie": "Apple consumer video editor",
    "iTerm": "Terminal emulator for macOS",
    "Keynote": "Apple presentation software",
    "Keychain Access": "macOS password and certificate manager",
    "Linear": "Project and issue tracking tool",
    "Logseq": "Open-source knowledge management and note-taking",
    "macOS Sequoia": "macOS installer",
    "macOS Sonoma": "macOS installer",
    "macOS Ventura": "macOS installer",
    "Mail": "Apple email client",
    "Maps": "Apple maps and navigation",
    "Messages": "Apple messaging (iMessage/SMS)",
    "Microsoft Excel": "Spreadsheet application",
    "Microsoft Outlook": "Email and calendar client",
    "Microsoft PowerPoint": "Presentation software",
    "Microsoft Teams": "Business communication platform",
    "Microsoft Word": "Word processor",
    "Migration Assistant": "macOS data transfer tool",
    "Music": "Apple music player (iTunes successor)",
    "News": "Apple news aggregator",
    "Notes": "Apple note-taking app",
    "Notion": "All-in-one workspace and note-taking",
    "Numbers": "Apple spreadsheet application",
    "OBS": "Open-source streaming and recording software",
    "Obsidian": "Markdown-based knowledge management",
    "OmniFocus": "Task management and GTD app",
    "Pages": "Apple word processor",
    "Photo Booth": "Apple webcam photo app",
    "Photos": "Apple photo library and editor",
    "Podcasts": "Apple podcast player",
    "Postman": "API development and testing tool",
    "Preview": "macOS image and PDF viewer",
    "QuickTime Player": "Apple media player and screen recorder",
    "Raycast": "Productivity launcher and extensible tool",
    "Reminders": "Apple task and reminder manager",
    "Safari": "Apple web browser",
    "Screenshot": "macOS screenshot utility",
    "Shortcuts": "Apple automation via shortcuts",
    "Signal": "Encrypted messaging app",
    "Siri": "Apple voice assistant",
    "Slack": "Team messaging and collaboration platform",
    "Spotify": "Music streaming service",
    "Stickies": "Apple desktop sticky notes",
    "Stocks": "Apple stock market tracker",
    "System Information": "macOS hardware/software info viewer",
    "System Preferences": "macOS settings panel",
    "System Settings": "macOS settings panel (Ventura+)",
    "TablePlus": "Database management GUI",
    "Terminal": "macOS built-in terminal emulator",
    "TextEdit": "Apple basic text and rich text editor",
    "Time Machine": "macOS backup utility",
    "Tower": "Git GUI client",
    "Transmission": "Open-source BitTorrent client",
    "TV": "Apple video streaming and library",
    "Utilities": "macOS system utility folder",
    "Visual Studio Code": "Source code editor by Microsoft",
    "VLC": "Open-source cross-platform media player",
    "Warp": "Modern terminal with AI features",
    "Weather": "Apple weather forecasting app",
    "WhatsApp": "Meta messaging and calling app",
    "Xcode": "Apple IDE for macOS/iOS development",
    "Zoom": "Video conferencing platform",
    "Zotero": "Reference management and bibliography tool",
}


def get_app_description(
    app_name: str,
    app_base: str = "",
    cask_map: dict[str, Any] | None = None,
    cask_descriptions: dict[str, str] | None = None,
    mdls_map: dict[str, Any] | None = None,
) -> str:
    """Get description for a GUI app from multiple sources.

    Priority:
    1. Hardcoded KNOWN_APP_DESCRIPTIONS
    2. Homebrew cask description
    3. mdls kMDItemKind
    4. Empty string (fallback)
    """
    if app_name in KNOWN_APP_DESCRIPTIONS:
        return KNOWN_APP_DESCRIPTIONS[app_name]

    if cask_map and cask_descriptions and app_base in cask_map:
        token = cask_map[app_base][0]
        if token in cask_descriptions:
            return cask_descriptions[token]

    if mdls_map and app_base in mdls_map:
        mdls_entry = mdls_map[app_base]
        kind = mdls_entry[2] if len(mdls_entry) > 2 else "(null)"
        if kind and kind not in ("(null)", "null", ""):
            return kind

    return ""
