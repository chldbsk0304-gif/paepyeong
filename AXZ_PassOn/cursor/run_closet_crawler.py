# -*- coding: utf-8 -*-
"""디지털 옷장 크롤러 진입점: 사이트 선택 → 수동 로그인 대기 → 수집 (Python 3.9 호환)."""
from __future__ import annotations

import asyncio
import sys
from typing import Any, Dict, List

from config import SITE_CONFIGS
from crawlers import MusinsaCrawler, ZigzagCrawler


def main() -> None:
    sites = list(SITE_CONFIGS.keys())
    if len(sys.argv) > 1 and sys.argv[1] in sites:
        site_key = sys.argv[1]
    else:
        print("사이트를 선택하세요:", ", ".join(sites))
        site_key = input("입력 (예: musinsa 또는 zigzag): ").strip().lower()
        if site_key not in sites:
            print(f"지원 사이트: {', '.join(sites)}")
            sys.exit(1)

    if site_key == "musinsa":
        crawler = MusinsaCrawler()
    else:
        crawler = ZigzagCrawler()

    async def run() -> List[Dict[str, Any]]:
        return await crawler.run(headless=False, open_folder_on_success=True)

    try:
        results = asyncio.run(run())
        print(f"수집 완료: {len(results)}건. 이미지 선택기는 image_selector 앱을 실행하세요.")
    except Exception as e:
        # 상세 대기는 BaseCrawler.run()에서 처리 (창 유지).
        print(f"[ERROR] 실행 중 예외 발생: {e!r}")
        raise


if __name__ == "__main__":
    main()
