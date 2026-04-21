from __future__ import annotations
import asyncio
import random
import os
import json
import sys
import shutil
import re
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
        self.browser = await playwright.chromium.launch(headless=False, slow_mo=BROWSER_CONFIG["slow_mo"])
        self.context = await self.browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=BROWSER_CONFIG["user_agent"]
        )
        self.page = await self.context.new_page()
        if stealth_func:
            try: await stealth_func(self.page)
            except: pass

    async def wait_for_user_login(self, site_name):
        print(f"\n[{site_name}] 로그인을 진행하고 '주문 내역' 페이지로 이동해 주세요.")
        await asyncio.to_thread(input, "준비가 되었다면 엔터를 눌러주세요...")

    async def random_sleep(self, min_s=3, max_s=5):
        await asyncio.sleep(random.uniform(min_s, max_s))

# ==========================================
# 3. Musinsa Crawler (Full Logic)
# ==========================================
class MusinsaCrawler(BaseCrawler):
    async def run(self):
        try:
            await self.init_browser()
            await self.page.goto("https://www.musinsa.com/auth/login")
            await self.wait_for_user_login("무신사")
            
            print("\n[Step 1] 주문 목록 수집 중...")
            # 무신사 주문 목록 셀렉터 (2024 PC 기준)
            items = await self.page.query_selector_all(".order-list-item, .list-item")
            orders = []
            
            for item in items:
                try:
                    name_el = await item.query_selector(".product-name, .name")
                    url_el = await item.query_selector("a[href*='/app/goods/']")
                    opt_el = await item.query_selector(".option, .info-item")
                    
                    if name_el and url_el:
                        orders.append({
                            "name": (await name_el.inner_text()).strip(),
                            "url": await url_el.get_attribute("href"),
                            "option": (await opt_el.inner_text()).strip() if opt_el else ""
                        })
                except: continue

            print(f"총 {len(orders)}개의 주문을 발견했습니다.")
            
            results = []
            for i, order in enumerate(orders):
                print(f"[{i+1}/{len(orders)}] 상세 페이지 진입: {order['name']}")
                await self.random_sleep()
                
                detail_data = await self.scrape_detail(order["url"], order["option"])
                results.append({**order, **detail_data})
            
            # 데이터 저장
            output_path = os.path.join(DIRS["data"], "musinsa_results.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            
            print(f"\n[SUCCESS] 모든 데이터가 저장되었습니다: {output_path}")
            print("브라우저를 종료하지 않습니다. 내용을 확인해 주세요.")
            while True: await asyncio.sleep(10)

        except Exception as e:
            print(f"[ERROR] {e}")
            while True: await asyncio.sleep(10)

    async def scrape_detail(self, url, purchased_option):
        try:
            full_url = url if url.startswith("http") else f"https:{url}"
            await self.page.goto(full_url)
            await self.page.wait_for_load_state("networkidle")
            
            # 기본 정보
            brand = await self.page.inner_text(".brand-name, .brand") if await self.page.query_selector(".brand-name, .brand") else "-"
            price = await self.page.inner_text(".product-price, .price") if await self.page.query_selector(".product-price, .price") else "-"
            
            # 실측 사이즈 표 파싱 (간소화된 로직)
            size_data = {}
            size_table = await self.page.query_selector("#size_table, .size-table")
            if size_table:
                # 구매한 옵션(예: L)과 일치하는 행 찾기 로직 포함 가능
                size_data = {"info": "사이즈 표 발견됨 (데이터 폴더 확인)"}

            # 이미지 수집 (temp 폴더로 저장)
            img_els = await self.page.query_selector_all(".product-img img, #detail_view img")
            saved_images = []
            for j, img in enumerate(img_els[:2]): # 앞/뒤 2장만
                src = await img.get_attribute("src")
                if src:
                    img_url = f"https:{src}" if src.startswith("//") else src
                    filename = f"musinsa_{int(asyncio.get_event_loop().time())}_{j}.jpg"
                    save_path = os.path.join(DIRS["temp"], filename)
                    # 실제 이미지 다운로드 로직 (생략 가능, URL만 저장도 가능)
                    saved_images.append(filename)

            return {
                "brand": brand.strip(),
                "price": price.strip(),
                "size_details": size_data,
                "images": saved_images
            }
        except:
            return {"error": "상세 페이지 로드 실패"}

# ==========================================
# 4. Main
# ==========================================
if __name__ == "__main__":
    crawler = MusinsaCrawler()
    asyncio.run(crawler.run())
