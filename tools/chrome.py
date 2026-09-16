#!/usr/bin/env python3
"""Locate a Chrome/Chromium/Edge binary and take headless screenshots with it.

Lettering and trailer statics are rendered as HTML and screenshotted, so every
headless render goes through find_chrome(). Set KAV_CHROME to override the search.
Run directly to print which browser was found.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

MAC_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]
WINDOWS_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge", "chrome"]


def find_chrome():
    env = os.environ.get("KAV_CHROME", "").strip()
    if env:
        if Path(env).exists() or shutil.which(env):
            return shutil.which(env) or env
        sys.exit(f"KAV_CHROME is set to '{env}' but nothing is there.")
    for p in MAC_PATHS + WINDOWS_PATHS:
        if Path(p).exists():
            return p
    for n in NAMES:
        found = shutil.which(n)
        if found:
            return found
    sys.exit("No Chrome/Chromium found. Kav renders lettering and slides with a headless browser.\n"
             "  Install Google Chrome or Chromium, or set KAV_CHROME=/path/to/chrome in .env or your shell.")


def screenshot(html_path, png_path, width, height, scale=1, budget_ms=15000):
    """Render a local HTML file to a PNG of width*scale x height*scale pixels."""
    cmd = [find_chrome(), "--headless=new", f"--screenshot={Path(png_path).resolve()}",
           f"--window-size={width},{height}", f"--force-device-scale-factor={scale}",
           "--hide-scrollbars", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
           f"--virtual-time-budget={budget_ms}", Path(html_path).resolve().as_uri()]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(2, "--no-sandbox")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not Path(png_path).exists():
        sys.exit(f"Headless render failed ({r.returncode}):\n{r.stderr[-800:]}")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(find_chrome())
