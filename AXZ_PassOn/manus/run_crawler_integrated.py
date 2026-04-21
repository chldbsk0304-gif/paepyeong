from __future__ import annotations
import asyncio
import random
import os
import json
import sys
import shutil
from playwright.async_api import async_playwright

# playwright_stealth 호환성 처리
try:
    from playwright_stealth import stealth_async as stealth_func
except ImportError:
    try:
        from playwright_stealth import stealth_page as stealth_func
    except ImportError:
        stealth_func = None

# ==========================================
# 1. Configuration
# ==========================================
ROOT_PATH = "/Users/kate.axz-pc/Desktop/AXZ_PassOn"
DIRS = {
    "images": os.path.join(ROOT_PATH, "images"),
    "temp": os.path.join(ROOT_PATH, "image_selector/static/temp"),
    "data": os.path.join(ROOT_PATH, "data"),
}

for p in DIRS.values():
    os.makedirs(p, exist_ok=True)

BROWSER_CONFIG = {
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "slow_mo": 150
}

# ==========================================
# 2. Base Crawler Class
# ==========================================
class BaseCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        playwright = await async_playwright().start()
        # 브라우저 실행 (사용자 확인을 위해 headless=False)
        self.browser = await playwright.chromium.launch(
            headless=False, 
            slow_mo=BROWSER_CONFIG["slow_mo"]
        )
        self.context = await self.browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=BROWSER_CONFIG["user_agent"]
        )
        self.page = await self.context.new_page()
        
        # Stealth 적용 (함수가 존재할 때만 실행)
        if stealth_func:
            try:
                await stealth_func(self.page)
                print("[INFO] Stealth mode applied.")
            except Exception as e:
                print(f"[WARN] Stealth application failed: {e}")
        else:
            print("[WARN] playwright-stealth functions not found. Running without stealth.")

    async def wait_for_user_login(self, site_name):
        print(f"\n[{site_name}] 로그인을 진행해 주세요.")
        print("주문 내역 화면으로 이동한 뒤 터미널에서 엔터를 눌러주세요.")
        await asyncio.to_thread(input, "엔터를 누르면 크롤링을 시작합니다...")

    async def handle_error(self, error):
        print(f"\n[ERROR] {error}")
        print("브라우저를 종료하지 않고 대기합니다. 원인을 확인하신 후 수동으로 종료해 주세요.")
        while True: 
            await asyncio.sleep(10)

# ==========================================
# 3. Musinsa Crawler
# ==========================================
class MusinsaCrawler(BaseCrawler):
    async def run(self):
        try:
            await self.init_browser()
            await self.page.goto("https://www.musinsa.com/auth/login")
            await self.wait_for_user_login("무신사")
            
            print("주문 내역 수집을 시작합니다...")
            # 여기에 실제 수집 로직이 들어갑니다.
            
            print("수집 완료.")
        except Exception as e:
            await self.handle_error(e)

# ==========================================
# 4. Main Execution
# ==========================================
async def main():
    print("=== AXZ_PassOn Integrated Crawler ===")
    print("1. 무신사 (Musinsa)")
    print("2. 지그재그 (Zigzag)")
    choice = input("선택 (1 또는 2): ")
    
    if choice == "1":
        crawler = MusinsaCrawler()
        await crawler.run()
    else:
        print("준비 중이거나 잘못된 선택입니다.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다.")
