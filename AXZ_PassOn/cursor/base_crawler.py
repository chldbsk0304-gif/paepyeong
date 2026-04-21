# -*- coding: utf-8 -*-
"""BaseCrawler: Playwright 초기화, Stealth, 경로 관리 (Python 3.9 호환)."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from config import BASE_PATH, IMAGES_DIR, TEMP_DIR, USER_DATA_DIR, ensure_dirs, get_site_config


# 최신 Chrome Desktop User-Agent (PC 화면 설정)
USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)
EXTRA_HEADERS: Dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


class BaseCrawler:
    """공통: Playwright 초기화, Stealth, 경로 관리. 사이트별 크롤러는 이를 상속."""

    def __init__(self, site_key: str) -> None:
        """
        site_key: 'musinsa' | 'zigzag'
        site_config는 get_site_config(site_key)로 로드하여 self.site_config에 보관.
        """
        self.site_key = site_key
        self.site_config: Dict[str, Any] = get_site_config(site_key)
        self._playwright: Optional[Any] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    @property
    def base_path(self) -> str:
        return BASE_PATH

    @property
    def images_dir(self) -> str:
        return IMAGES_DIR

    @property
    def temp_dir(self) -> str:
        return TEMP_DIR

    def _ensure_dirs(self) -> None:
        """저장 경로 디렉터리 생성."""
        ensure_dirs()

    async def _inject_advanced_stealth(self, page: Page) -> None:
        """고급 Stealth 스크립트 주입: navigator.webdriver, cdc_, languages, vendor, renderer 등."""
        stealth_script = """
        // navigator.webdriver 제거
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });

        // cdc_ 자동화 흔적 제거
        Object.keys(window).forEach(key => {
            if (key.includes('cdc_') || key.includes('__playwright') || key.includes('__pw')) {
                delete window[key];
            }
        });

        // navigator.languages (Mac 환경)
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });

        // navigator.vendor (Chrome)
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.'
        });

        // navigator.platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel'
        });

        // navigator.hardwareConcurrency (일반적인 Mac 값)
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });

        // navigator.deviceMemory (일반적인 Mac 값)
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });

        // Chrome 객체 추가
        window.chrome = {
            runtime: {}
        };

        // Permission API 조작
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // WebGL renderer 정보 (Mac 환경)
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
        """
        await page.add_init_script(stealth_script)

    async def _init_browser(self, headless: bool = False) -> None:
        """launch_persistent_context 사용: 실제 사용자 프로필과 유사한 환경 구축."""
        self._playwright = await async_playwright().start()

        # launch_persistent_context 옵션: user_data_dir 사용
        opts: Dict[str, Any] = {
            "user_data_dir": USER_DATA_DIR,
            "headless": headless,
            "slow_mo": 150,
            # PC 브라우저 환경 (모바일 에뮬레이션 관련 옵션 제거)
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": USER_AGENT,
            "extra_http_headers": EXTRA_HEADERS,
            "locale": "ko-KR",
            "ignore_https_errors": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        }
        # is_landscape 제거 (TypeError 방지)
        if "is_landscape" in opts:
            del opts["is_landscape"]

        # launch_persistent_context: 실제 사용자 프로필과 유사한 환경
        self._context = await self._playwright.chromium.launch_persistent_context(**opts)

        # playwright-stealth 적용 (설치된 경우)
        try:
            from playwright_stealth import Stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(self._context)
        except ImportError:
            pass

        # 첫 번째 페이지 가져오기 (persistent context는 이미 페이지가 있음)
        pages = self._context.pages
        if pages:
            self._page = pages[0]
        else:
            self._page = await self._context.new_page()

        # 고급 Stealth 스크립트 주입
        await self._inject_advanced_stealth(self._page)

    async def _close_browser(self) -> None:
        """브라우저·Playwright 정리."""
        # NOTE:
        # - 사용자 요구: 엔터 입력 직후/에러 발생 시에도 브라우저 창이 닫히지 않게 해야 함.
        # - 따라서 자동 close/stop을 수행하지 않음. (창은 사용자가 수동으로 닫음)
        #
        # if self._context:
        #     await self._context.close()
        #     self._context = None
        # if self._playwright:
        #     await self._playwright.stop()
        #     self._playwright = None
        # self._page = None
        return

    async def wait_for_manual_login(self, message: str = "브라우저에서 로그인 후 '주문 내역' 화면이 보이면 터미널에서 엔터를 눌러주세요: ") -> None:
        """
        로그인 페이지 접속 후, 유저가 직접 로그인 완료하고 '주문 내역' 화면을 띄울 때까지 무한 대기.
        프로그램은 로그인 시도하지 않음. 유저가 엔터를 누르면 쿠키·세션 유지한 채 수집 단계로 진행.
        """
        try:
            await asyncio.to_thread(input, message)
        except (EOFError, KeyboardInterrupt):
            pass

    async def run(
        self,
        headless: bool = False,
        open_folder_on_success: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        크롤링 실행 흐름: 브라우저 초기화 → 로그인 페이지 → 수동 로그인 대기 → 주문 목록 수집 → 정리.
        서브클래스에서 _do_crawl() 등을 오버라이드하여 사이트별 로직 구현.
        """
        self._ensure_dirs()
        await self._init_browser(headless=headless)
        try:
            results = await self._run_flow()
            if results and open_folder_on_success:
                os.system(f"open {BASE_PATH}")
            # 2차 대기: 수집 시도 종료 후 사용자가 창/에러 화면을 확인할 수 있게 유지
            await asyncio.to_thread(
                input,
                "수집 시도가 끝났습니다. 창을 확인하고 터미널에서 엔터를 눌러 종료하세요...",
            )
            return results
        except Exception as e:
            # 에러 발생 시 브라우저를 닫지 않고 유지 (수동으로 닫게 함)
            print(f"[ERROR] 크롤링 중 예외 발생: {e!r}")
            await asyncio.to_thread(
                input,
                "에러가 발생했습니다. 창을 확인하고 터미널에서 엔터를 눌러 종료하세요...",
            )
            raise

    async def _run_flow(self) -> List[Dict[str, Any]]:
        """실제 크롤링 플로우. 서브클래스에서 오버라이드."""
        raise NotImplementedError("Subclass must implement _run_flow()")
