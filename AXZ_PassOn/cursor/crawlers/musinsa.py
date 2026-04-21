# -*- coding: utf-8 -*-
"""무신사 구매 내역 크롤러 (Python 3.9 호환)."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional

from base_crawler import BaseCrawler


class MusinsaCrawler(BaseCrawler):
    """무신사 사이트 전용: BaseCrawler 상속, site_config 완벽 전달."""

    def __init__(self) -> None:
        super().__init__("musinsa")
        assert "login_url" in self.site_config
        assert "order_list_url" in self.site_config

    async def _run_flow(self) -> List[Dict[str, Any]]:
        """메인 페이지 → 대기 → 로그인 페이지 → 수동 로그인 대기 → 주문 내역 수집 → 이미지 temp 저장."""
        # temp 폴더 존재 여부 체크 및 강제 생성
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"[INIT] temp 폴더 확인/생성 완료: {self.temp_dir}")

        page = self._page
        if not page:
            return []

        base_url = self.site_config["base_url"]
        login_url = self.site_config["login_url"]
        order_list_url = self.site_config["order_list_url"]
        order_selector = self.site_config.get("order_list_selector", ".order-list")
        item_link_selector = self.site_config.get("item_link_selector", "a[href*='/app/goods/'], a[href*='/goods/']")
        image_selector = self.site_config.get("image_selector", "img[src*='goods']")

        # 1. 메인 페이지 먼저 접속 (자연스러운 접속 흐름)
        print(f"[STEP] 메인 페이지 접속: {base_url}")
        await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
        # 2. 3~5초 대기 (사용자 행동 패턴 흉내)
        import random
        wait_time = random.randint(3000, 5000)
        print(f"[WAIT] 메인 페이지 로딩 후 대기: {wait_time}ms")
        await page.wait_for_timeout(wait_time)

        # 3. 로그인 페이지로 이동 (프로그램은 로그인 시도 안 함, 모든 조작은 사용자가 직접)
        print(f"[STEP] 로그인 페이지 이동: {login_url}")
        await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
        await self.wait_for_manual_login(
            "무신사 로그인 후 '주문 내역' 화면이 보이면 터미널에서 엔터를 눌러주세요: "
        )
        # 4. 유저가 엔터를 누르면 쿠키·세션 유지한 채 주문 내역 페이지로 이동
        print(f"[STEP] 주문 내역 페이지 이동: {order_list_url}")
        await page.goto(order_list_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)

        results: List[Dict[str, Any]] = []
        print(f"[SCRAPE] 상품 리스트를 찾는 중 (Selector: {order_selector}) ...")
        try:
            order_blocks = await page.query_selector_all(order_selector)
        except Exception:
            order_blocks = await page.query_selector_all("main [class*='order'], [class*='Order']")
        if not order_blocks:
            order_blocks = [page]

        seen_hrefs: set = set()
        for block in order_blocks:
            print(f"[SCRAPE] 상품 링크를 찾는 중 (Selector: {item_link_selector}) ...")
            links = await block.query_selector_all(item_link_selector)
            print(f"[SCRAPE] 찾은 상품 개수(링크 기준): {len(links)}개")
            for link in links[:50]:
                href = await link.get_attribute("href")
                if not href or href in seen_hrefs:
                    continue
                if "/goods/" not in href and "/app/goods/" not in href:
                    continue
                seen_hrefs.add(href)
                if not href.startswith("http"):
                    base_url = self.site_config.get("base_url", "https://www.musinsa.com")
                    href = base_url.rstrip("/") + ("/" + href.lstrip("/") if not href.startswith("/") else href)
                title = await link.get_attribute("title") or (await link.inner_text()).strip() or "무신사 상품"
                title = re.sub(r'[\\/*?:"<>|]', "_", title)[:100]
                print(f"[SCRAPE] 상품명 추출 성공: {title}")
                results.append({"url": href, "title": title, "site": "musinsa"})

        print(f"[SCRAPE] 최종 수집 대상 상품 수: {len(results)}개")
        for i, item in enumerate(results[:20]):
            await self._save_item_images(item, image_selector, index=i)

        meta_path = os.path.join(self.temp_dir, "musinsa_orders.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return results

    async def _save_item_images(
        self,
        item: Dict[str, Any],
        image_selector: str,
        index: int,
    ) -> None:
        """상품 페이지 열어 이미지 URL 수집 후 temp에 저장."""
        page = self._page
        if not page:
            return
        url = item.get("url")
        title = item.get("title", "item")
        if not url:
            return
        try:
            print(f"[IMG] 이미지 다운로드 시도 중... ({index}) {title} / {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1500)
            imgs = await page.query_selector_all(image_selector)
            urls: List[str] = []
            for img in imgs[:15]:
                src = await img.get_attribute("src")
                if src and ("goods" in src or "product" in src or "http" in src):
                    if not src.startswith("http"):
                        src = self.site_config.get("base_url", "") + src
                    urls.append(src)
            if not urls:
                urls = await page.evaluate(
                    """() => Array.from(document.querySelectorAll('img'))
                        .map(i => i.src).filter(s => s && (s.includes('goods') || s.includes('product')))"""
                )
            print(f"[IMG] 후보 이미지 URL 개수: {len(urls)}개 (Selector: {image_selector})")
            for j, img_url in enumerate(urls[:10]):
                try:
                    print(f"[IMG] 다운로드 시도: {img_url}")
                    ext = "jpg"
                    if ".png" in img_url.lower():
                        ext = "png"
                    safe_title = re.sub(r'[\\/*?:"<>|]', "_", str(title))[:60]
                    filename = f"musinsa_{index}_{j}_{safe_title}.{ext}"
                    path = os.path.join(self.temp_dir, filename)
                    urllib.request.urlretrieve(img_url, path)
                    if not item.get("local_paths"):
                        item["local_paths"] = []
                    item["local_paths"].append(path)
                except Exception:
                    continue
        except Exception:
            pass
