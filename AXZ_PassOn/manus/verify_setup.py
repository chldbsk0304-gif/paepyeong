from __future__ import annotations
import os
import asyncio
from playwright.async_api import async_playwright
from config import DIRS, SITES

async def verify():
    print("=== Verification Start ===")
    
    # 1. Folder Check
    for name, path in DIRS.items():
        if os.path.exists(path):
            print(f"[OK] Folder exists: {name} -> {path}")
        else:
            print(f"[FAIL] Folder missing: {name} -> {path}")

    # 2. Browser & Login Page Check
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print(f"Connecting to Musinsa Login: {SITES['musinsa']['login_url']}")
            await page.goto(SITES['musinsa']['login_url'], timeout=30000)
            title = await page.title()
            print(f"[OK] Musinsa Page Title: {title}")
            
            await browser.close()
    except Exception as e:
        print(f"[FAIL] Browser test failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
