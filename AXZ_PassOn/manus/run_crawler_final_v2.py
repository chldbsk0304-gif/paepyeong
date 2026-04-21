from __future__ import annotations
import asyncio
import random
import os
import json
import sys
import requests
from playwright.async_api import async_playwright

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

# ==========================================
# 2. Crawler Logic
# ==========================================
class MusinsaCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await self.context.new_page()

    async def download_image(self, url, filename):
        try:
            if not url: return False
            full_url = f"https:{url}" if url.startswith("//") else url
            save_path = os.path.join(DIRS["temp"], filename)
            
            # Playwright의 page.screenshot 대신 requests나 직접 저장을 시도
            response = requests.get(full_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"  [이미지 저장 실패] {e}")
        return False

    async def run(self):
        try:
            await self.init_browser()
            await self.page.goto("https://www.musinsa.com/auth/login")
            
            print("\n[알림] 로그인을 완료하고 '주문 내역' 페이지로 이동해 주세요.")
            input("준비가 되었다면 터미널에서 엔터를 눌러주세요...")

            print("\n[Step 1] 주문 목록 분석 중...")
            # 무신사 주문 목록의 다양한 셀렉터 시도
            await self.page.wait_for_selector("body")
            items = await self.page.query_selector_all("li[class*='order-list'], .list-item, .order-item")
            
            if not items:
                print("[경고] 주문 항목을 찾지 못했습니다. 페이지 구조가 변경되었거나 로그인 상태가 아닐 수 있습니다.")
                # 디버깅을 위해 현재 페이지의 텍스트 일부 출력
                content = await self.page.inner_text("body")
                print(f"현재 페이지 요약: {content[:100]}...")
            
            orders = []
            for item in items:
                # 상품명 및 URL 추출 시도
                name_el = await item.query_selector("p[class*='name'], .product-name, a[href*='/goods/']")
                url_el = await item.query_selector("a[href*='/goods/']")
                
                if name_el and url_el:
                    name = (await name_el.inner_text()).strip()
                    url = await url_el.get_attribute("href")
                    orders.append({"name": name, "url": url})

            print(f"총 {len(orders)}개의 주문 상품을 찾았습니다.")

            results = []
            for i, order in enumerate(orders):
                print(f"[{i+1}/{len(orders)}] 상세 수집 중: {order['name']}")
                await self.page.goto(f"https://www.musinsa.com{order['url']}" if order['url'].startswith('/') else order['url'])
                await asyncio.sleep(random.uniform(2, 4))

                # 상세 정보 추출
                brand = await self.page.inner_text(".brand-name, .brand") if await self.page.query_selector(".brand-name, .brand") else "미확인"
                price = await self.page.inner_text(".product-price, .price") if await self.page.query_selector(".product-price, .price") else "미확인"
                
                # 이미지 추출 및 저장
                img_els = await self.page.query_selector_all(".product-img img, .thumb img")
                saved_imgs = []
                for idx, img in enumerate(img_els[:2]):
                    src = await img.get_attribute("src")
                    fname = f"item_{i}_{idx}.jpg"
                    if await self.download_image(src, fname):
                        saved_imgs.append(fname)

                results.append({
                    "상품명": order['name'],
                    "브랜드": brand.strip(),
                    "가격": price.strip(),
                    "이미지": saved_imgs,
                    "URL": order['url']
                })

            # 결과 저장
            output_path = os.path.join(DIRS["data"], "musinsa_data.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            
            print(f"\n[완료] {len(results)}개의 데이터가 저장되었습니다: {output_path}")
            print("터미널을 종료하지 마시고 브라우저에서 결과를 확인해 보세요.")
            await asyncio.sleep(3600)

        except Exception as e:
            print(f"\n[오류 발생] {e}")
            await asyncio.sleep(3600)

if __name__ == "__main__":
    crawler = MusinsaCrawler()
    asyncio.run(crawler.run())
