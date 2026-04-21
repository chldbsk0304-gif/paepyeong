from __future__ import annotations
import asyncio
import random
import os
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from config import BROWSER_CONFIG, DIRS

class BaseCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False, 
            slow_mo=BROWSER_CONFIG["slow_mo"]
        )
        self.context = await self.browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=BROWSER_CONFIG["user_agent"]
        )
        self.page = await self.context.new_page()
        await stealth_async(self.page)

    async def random_sleep(self, min_sec=3, max_sec=5):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def wait_for_user_login(self, site_name):
        print(f"[{site_name}] 로그인을 진행해 주세요. 주문 내역 화면으로 이동한 뒤 엔터를 눌러주세요.")
        await asyncio.to_thread(input, "엔터를 누르면 크롤링을 시작합니다...")

    async def save_image(self, url, filename, is_temp=True):
        target_dir = DIRS["temp"] if is_temp else DIRS["images"]
        path = os.path.join(target_dir, filename)
        # 이미지 저장 로직 (상세 구현은 사이트별 크롤러에서 수행)
        return path

    async def handle_error(self, error):
        print(f"Error occurred: {error}")
        print("브라우저를 종료하지 않고 대기합니다. 원인을 확인하신 후 수동으로 종료해 주세요.")
        while True:
            await asyncio.sleep(10)
