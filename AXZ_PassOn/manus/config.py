from __future__ import annotations
import os

# Base Path
ROOT_PATH = "/Users/kate.axz-pc/Desktop/AXZ_PassOn"

# Directories
DIRS = {
    "images": os.path.join(ROOT_PATH, "images"),
    "temp": os.path.join(ROOT_PATH, "image_selector/static/temp"),
    "data": os.path.join(ROOT_PATH, "data"),
}

# Ensure directories exist
for path in DIRS.values():
    os.makedirs(path, exist_ok=True)

# Site Selectors & URLs
SITES = {
    "musinsa": {
        "login_url": "https://www.musinsa.com/auth/login",
        "order_list_url": "https://www.musinsa.com/mypage/order/list",
        "selectors": {
            "order_items": ".order-list-item",
            "product_name": ".product-name",
            "product_url": ".product-name a",
            "size_option": ".option",
            "detail": {
                "brand": ".brand-name",
                "price": ".product-price",
                "size_table": ".size-table",
                "images": ".product-img img"
            }
        }
    },
    "zigzag": {
        "login_url": "https://zigzag.kr/login",
        "order_list_url": "https://zigzag.kr/mypage/order-list",
        "selectors": {
            "order_items": "[class*='OrderItem']",
            "product_name": "[class*='ProductName']",
            "product_url": "a[href*='/catalog/products/']",
            "size_option": "[class*='OptionText']",
            "detail": {
                "brand": "[class*='BrandName']",
                "price": "[class*='PriceText']",
                "size_table": "[class*='SizeTable']",
                "images": "[class*='ProductImage'] img"
            }
        }
    }
}

# Browser Config
BROWSER_CONFIG = {
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "slow_mo": 150
}
