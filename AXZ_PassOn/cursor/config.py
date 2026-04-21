# -*- coding: utf-8 -*-
"""디지털 옷장 크롤러 설정 (Python 3.9 호환)."""
from __future__ import annotations

import os
from typing import Any, Dict, List

# 프로젝트 절대 경로 (저장·이미지 경로 고정)
BASE_PATH: str = "/Users/kate.axz-pc/Desktop/AXZ_PassOn"

# 하위 디렉터리
IMAGES_DIR: str = os.path.join(BASE_PATH, "images")
TEMP_DIR: str = os.path.join(BASE_PATH, "image_selector", "static", "temp")
USER_DATA_DIR: str = os.path.join(BASE_PATH, "user_data")


def ensure_dirs() -> None:
    """images, image_selector/static/temp, user_data 폴더 강제 생성."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(USER_DATA_DIR, exist_ok=True)


# 사이트별 설정 (BaseCrawler에서 site_config로 전달)
SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "musinsa": {
        "name": "무신사",
        "base_url": "https://www.musinsa.com",
        "login_url": "https://www.musinsa.com/app/auth/login",
        "order_list_url": "https://www.musinsa.com/app/my/order",
        # PC 버전 주문/주문내역 화면 대비: 여러 후보 selector를 폭넓게 지정
        "order_list_selector": (
            "#myOrder, #myOrderList, #orderList, "
            ".order-list, .my-order-list, .my-order, "
            "main [class*='order'], [data-testid*='order'], [class*='Order']"
        ),
        "item_link_selector": (
            "a[href*='/app/goods/'], a[href*='/goods/'], "
            "a[href*='/product/'], a[href*='goodsNo=']"
        ),
        "image_selector": "img[src*='goods'], .detail-img img, .product-img img",
    },
    "zigzag": {
        "name": "지그재그",
        "base_url": "https://www.zigzag.kr",
        "login_url": "https://www.zigzag.kr/login",
        "order_list_url": "https://www.zigzag.kr/mypage/order",
        "order_list_selector": (
            "#orderList, #mypageOrder, "
            ".order-list, .mypage-order, .my-order, "
            "main [class*='order'], [data-testid*='order'], [class*='Order']"
        ),
        "item_link_selector": (
            "a[href*='/product/'], a[href*='/shop/'], "
            "a[href*='productId='], a[href*='goodsNo=']"
        ),
        "image_selector": "img[src*='product'], .product-img img, .detail-img img",
    },
}


def get_site_config(site_key: str) -> Dict[str, Any]:
    """사이트 키로 설정 딕셔너리 반환."""
    if site_key not in SITE_CONFIGS:
        raise ValueError(f"Unknown site: {site_key}. Available: {list(SITE_CONFIGS.keys())}")
    return SITE_CONFIGS[site_key].copy()
