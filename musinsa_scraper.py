# 카테고리 추가: categories 딕셔너리에 추가
# 수집 개수 변경: per_category 숫자 변경
# 실행: python3 musinsa_scraper.py

import asyncio
import os
import re
import sys
import json
from playwright.async_api import async_playwright

# 스크립트 파일 위치 기준으로 경로 고정 (어디서 실행해도 항상 프로젝트 폴더에 저장)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

categories = {
    "상의":        "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=001000&ageBand=AGE_BAND_ALL&subPan=product",
    "아우터":      "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=002000&ageBand=AGE_BAND_ALL&subPan=product",
    "바지":        "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=003000&ageBand=AGE_BAND_ALL&subPan=product",
    "원피스/스커트": "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=100000&ageBand=AGE_BAND_ALL&subPan=product",
    "가방":        "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=004000&ageBand=AGE_BAND_ALL&subPan=product",
    "소품":        "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=101000&ageBand=AGE_BAND_ALL&subPan=product",
    "신발":        "https://www.musinsa.com/main/musinsa/ranking?gf=F&storeCode=musinsa&sectionId=200&contentsId=&categoryCode=103000&ageBand=AGE_BAND_ALL&subPan=product",
}

per_category = 50  # 카테고리당 수집할 상품 수

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


async def collect_urls(page, category, ranking_url, count):
    print(f"🔍 {category} 랭킹 URL 수집중...")
    try:
        await page.goto(ranking_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)

        hrefs = await page.evaluate(
            """(count) => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/products/"]'));
                const seen = new Set();
                const result = [];
                for (const a of anchors) {
                    const url = a.href.split('?')[0];
                    if (!seen.has(url) && /\\/products\\/\\d+/.test(url)) {
                        seen.add(url);
                        result.push(url);
                        if (result.length >= count) break;
                    }
                }
                return result;
            }""",
            count,
        )

        print(f"✅ {category}: {len(hrefs)}개 URL 수집완료")
        return hrefs

    except Exception as e:
        print(f"❌ {category} URL 수집 실패: {e}")
        return []


async def scrape_product(page, url, category):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        name = await page.evaluate(
            "() => { const m = document.querySelector('meta[property=\"og:title\"]'); return m ? m.content : null; }"
        )

        brand = await page.evaluate(
            """() => {
                const m = document.querySelector('meta[property="og:site_name"]');
                if (m && m.content) return m.content;
                const el = document.querySelector('.brand-name, [class*="brand"]');
                return el ? el.innerText.trim() : null;
            }"""
        )

        price_raw = await page.evaluate(
            """() => {
                const els = Array.from(document.querySelectorAll('[class*="price"]'));
                for (const el of els) {
                    const text = el.innerText.replace(/[^0-9]/g, '');
                    if (text.length >= 4) return text;
                }
                return null;
            }"""
        )
        price = int(price_raw) if price_raw else None

        image_url = await page.evaluate(
            """() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const match = imgs.find(img => img.src && img.src.includes('msscdn.net'));
                return match ? match.src : null;
            }"""
        )

        if not name:
            raise ValueError("상품명 없음")

        product = {
            "brand": brand or "",
            "name": name,
            "category": category,
            "price": price,
            "imageUrl": image_url or "",
            "url": url,
            "tags": [],
        }
        print(f"✅ 수집완료: {name}")
        return product

    except Exception as e:
        print(f"❌ 실패: {url} ({e})")
        return None


def is_valid(p):
    return bool(p.get("name")) and bool(p.get("imageUrl")) and bool(p.get("brand"))


def to_js(products):
    lines = ["var dummyProducts = ["]
    for i, p in enumerate(products):
        comma = "," if i < len(products) - 1 else ""
        lines.append("  {")
        lines.append(f"    id: {i + 1},")
        lines.append(f"    brand: {json.dumps(p['brand'], ensure_ascii=False)},")
        lines.append(f"    name: {json.dumps(p['name'], ensure_ascii=False)},")
        lines.append(f"    category: {json.dumps(p['category'], ensure_ascii=False)},")
        lines.append(f"    price: {p['price'] if p['price'] is not None else 'null'},")
        lines.append(f"    imageUrl: {json.dumps(p['imageUrl'], ensure_ascii=False)},")
        lines.append(f"    url: {json.dumps(p['url'], ensure_ascii=False)},")
        lines.append("    tags: [],")
        lines.append(f"  }}{comma}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def parse_js_products(content):
    products = []
    current = {}
    in_product = False

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped == "{":
            current = {}
            in_product = True
        elif stripped in ("},", "}"):
            if in_product and current:
                products.append(current)
            in_product = False
            current = {}
        elif in_product:
            m = re.match(r"(\w+):\s*(.*?),?\s*$", stripped)
            if m:
                key, val = m.group(1), m.group(2).rstrip(",").strip()
                if val.startswith('"') and val.endswith('"'):
                    current[key] = json.loads(val)
                elif val == "null":
                    current[key] = None
                elif val == "[]":
                    current[key] = []
                else:
                    try:
                        current[key] = int(val)
                    except ValueError:
                        current[key] = val

    return products


def cleanup_js(output_path):
    if not os.path.exists(output_path):
        print(f"파일 없음: {output_path}")
        return

    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    before = parse_js_products(content)
    after = [p for p in before if is_valid(p)]
    removed = len(before) - len(after)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(to_js(after))

    print(f"✅ 정리완료! {removed}개 항목 삭제 → 총 {len(after)}개 상품 남음")


async def main():
    products = []
    output_path = os.path.join(SCRIPT_DIR, "src", "data", "dummyProducts.js")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()

        for category, ranking_url in categories.items():
            product_urls = await collect_urls(page, category, ranking_url, per_category)

            if not product_urls:
                continue

            for url in product_urls:
                result = await scrape_product(page, url, category)
                if result:
                    products.append(result)

        await browser.close()

    valid_products = [p for p in products if is_valid(p)]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(to_js(valid_products))

    print(f"✅ 최종완료! {len(valid_products)}개 상품 → {output_path} 저장됨")


if __name__ == "__main__":
    output_path = os.path.join(SCRIPT_DIR, "src", "data", "dummyProducts.js")
    if "--clean" in sys.argv:
        cleanup_js(output_path)
    else:
        asyncio.run(main())
