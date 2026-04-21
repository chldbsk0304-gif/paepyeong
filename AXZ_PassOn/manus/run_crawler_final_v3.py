from __future__ import annotations
import asyncio
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
# 2. Crawler Logic (V3: Force Extraction)
# ==========================================
class MusinsaCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

    async def run(self):
        try:
            await self.init_browser()
            await self.page.goto("https://www.musinsa.com/auth/login")
            
            print("\n" + "="*50)
            print("[필독] 로그인을 완료하고 '주문 내역' 페이지로 이동해 주세요.")
            print("상품 목록이 화면에 보일 때 터미널에서 엔터를 눌러주세요.")
            print("="*50)
            input("엔터를 누르면 수집을 시작합니다...")

            print("\n[Step 1] 페이지 전체 분석 중...")
            
            # 방식 1: 모든 링크 중 상품 상세 페이지 패턴 추출
            links = await self.page.query_selector_all("a")
            order_links = []
            seen_urls = set()
            
            for link in links:
                href = await link.get_attribute("href")
                if href and ("/app/goods/" in href or "/goods/" in href):
                    # 중복 제거 및 절대 경로 처리
                    full_url = f"https://www.musinsa.com{href}" if href.startswith("/") else href
                    clean_url = full_url.split("?")[0]
                    if clean_url not in seen_urls:
                        # 부모 요소에서 상품명 추출 시도
                        text = await link.inner_text()
                        if len(text.strip()) > 2: # 의미 있는 텍스트가 있는 경우만
                            order_links.append({"name": text.strip(), "url": clean_url})
                            seen_urls.add(clean_url)

            if not order_links:
                print("[오류] 상품 링크를 찾지 못했습니다. 화면에 주문 내역이 보이는지 확인해 주세요.")
                # 강제 스크린샷 저장 (디버깅용)
                await self.page.screenshot(path=os.path.join(DIRS["data"], "debug_screen.png"))
                print(f"현재 화면을 {DIRS['data']}/debug_screen.png 에 저장했습니다. 확인해 보세요.")
                return

            print(f"총 {len(order_links)}개의 상품 링크를 발견했습니다.")

            results = []
            for i, order in enumerate(order_links):
                print(f"[{i+1}/{len(order_links)}] 상세 정보 추출 중: {order['name'][:20]}...")
                
                # 상세 페이지 이동
                detail_page = await self.context.new_page()
                try:
                    await detail_page.goto(order["url"], wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)
                    
                    # 브랜드, 가격 추출 (다양한 셀렉터 시도)
                    brand = "미확인"
                    for selector in [".brand-name", ".brand", ".product-detail__brand-name"]:
                        el = await detail_page.query_selector(selector)
                        if el: 
                            brand = await el.inner_text()
                            break
                    
                    price = "미확인"
                    for selector in [".product-price", ".price", "#goods_price"]:
                        el = await detail_page.query_selector(selector)
                        if el:
                            price = await el.inner_text()
                            break

                    # 이미지 저장
                    img_els = await detail_page.query_selector_all("img[src*='goods_img'], .product-img img")
                    saved_imgs = []
                    for idx, img in enumerate(img_els[:2]):
                        src = await img.get_attribute("src")
                        if src:
                            img_url = f"https:{src}" if src.startswith("//") else src
                            fname = f"item_{i}_{idx}.jpg"
                            save_path = os.path.join(DIRS["temp"], fname)
                            try:
                                res = requests.get(img_url, timeout=10)
                                with open(save_path, "wb") as f: f.write(res.content)
                                saved_imgs.append(fname)
                            except: pass

                    results.append({
                        "상품명": order["name"],
                        "브랜드": brand.strip(),
                        "가격": price.strip(),
                        "URL": order["url"],
                        "이미지": saved_imgs
                    })
                except Exception as e:
                    print(f"  [상세 페이지 오류] {e}")
                finally:
                    await detail_page.close()

            # 최종 저장
            output_path = os.path.join(DIRS["data"], "musinsa_final_results.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            
            print(f"\n[성공] {len(results)}개의 상품 정보가 저장되었습니다!")
            print(f"파일 위치: {output_path}")
            print("브라우저를 닫지 마시고 터미널을 확인해 주세요.")
            await asyncio.sleep(3600)

        except Exception as e:
            print(f"\n[치명적 오류] {e}")
            await asyncio.sleep(3600)

if __name__ == "__main__":
    crawler = MusinsaCrawler()
    asyncio.run(crawler.run())
