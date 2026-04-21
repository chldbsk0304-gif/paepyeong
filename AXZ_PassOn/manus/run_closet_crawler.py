from __future__ import annotations
import asyncio
import sys
import os

# 프로젝트 루트 경로를 sys.path에 추가하여 모듈 참조 해결
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from crawlers.musinsa import MusinsaCrawler
from crawlers.zigzag import ZigzagCrawler

async def main():
    print("=== AXZ_PassOn Closet Crawler ===")
    print("1. 무신사 (Musinsa)")
    print("2. 지그재그 (Zigzag)")
    choice = input("크롤링할 사이트 번호를 선택하세요: ")

    if choice == "1":
        crawler = MusinsaCrawler()
    elif choice == "2":
        crawler = ZigzagCrawler()
    else:
        print("잘못된 선택입니다.")
        return

    await crawler.run()

if __name__ == "__main__":
    asyncio.run(main())
