# 디지털 옷장 크롤러

무신사·지그재그 구매 내역 수집 후, 앞/뒷면 등 원하는 옷 사진을 선택해 저장하는 시스템입니다.

## 환경

- macOS, Python 3.9
- 프로젝트 경로: `/Users/kate.axz-pc/Desktop/AXZ_PassOn`
- 저장 경로: `config.py`의 `BASE_PATH` (기본: `/Users/kate.axz-pc/Desktop/AXZ_PassOn`)

## 설치 (pip)

프로젝트 루트에서:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 필요한 패키지 목록 (직접 설치 시)

```bash
pip install "playwright>=1.40.0"
pip install "playwright-stealth>=2.0.0"
pip install "flask>=2.3.0"
playwright install chromium
```

## 실행 방법

1. **크롤러 실행** (프로젝트 루트에서)

   ```bash
   python run_closet_crawler.py
   # 또는 사이트 지정
   python run_closet_crawler.py musinsa
   python run_closet_crawler.py zigzag
   ```

   - 브라우저가 열리면 해당 쇼핑몰에서 **직접 로그인**한 뒤, 주문 내역 화면이 보이면 **터미널에서 엔터**를 누릅니다.
   - 프로그램은 로그인을 시도하지 않으며, 로그인 페이지로 이동만 합니다. 유저가 직접 로그인 완료 후 엔터를 누르면 쿠키·세션을 유지한 채 수집을 진행합니다.
   - Viewport: `390x1200` (하단 탭바·네비게이션 보이도록), `device_scale_factor: 2` (고해상도), `slow_mo: 150ms` (사람 동작 속도 흉내)
   - 수집이 끝나면 `BASE_PATH` 폴더가 자동으로 열리고, 이미지는 `image_selector/static/temp`에 저장됩니다.

2. **이미지 선택기 실행** (저장할 앞/뒷면 등 선택)

   ```bash
   python image_selector/app.py
   # 또는
   flask --app image_selector.app run
   ```

   - 브라우저에서 http://127.0.0.1:5000 접속 후, temp 이미지 중 저장할 항목을 선택하고 **「선택한 이미지를 옷장(images)에 저장」**을 누릅니다.
   - 선택한 파일은 `shutil.move`로 `AXZ_PassOn/images` 폴더로 이동하며, 저장 후 `os.path.exists` 및 경로 검증(`AXZ_PassOn/images` 내부인지 확인)으로 기록 여부를 검증합니다.

## 주요 기능

- **Anti-Bot 우회**: `playwright-stealth`, iPhone 15 Pro User-Agent, `slow_mo=150ms`로 사람의 동작 속도 흉내
- **수동 로그인**: 프로그램은 로그인 시도하지 않음. 유저가 직접 로그인 후 엔터 입력 시 쿠키·세션 유지
- **화면 최적화**: Viewport `390x1200` (하단 탭바 보이도록), `device_scale_factor: 2` (고해상도)
- **경로 검증**: 이미지 저장 시 `AXZ_PassOn/images`로 정확히 이동하는지 검증

## 폴더 구조

- `config.py`: 절대 경로 (`BASE_PATH = /Users/kate.axz-pc/Desktop/AXZ_PassOn`), 사이트별 설정
- `base_crawler.py`: Playwright·Stealth·경로 공통 로직 (viewport, slow_mo, UA 설정)
- `crawlers/musinsa.py`, `crawlers/zigzag.py`: 사이트별 크롤러 (로그인 플로우 단순화)
- `run_closet_crawler.py`: 크롤러 진입점
- `image_selector/app.py`: Flask 이미지 선택기 (temp → AXZ_PassOn/images, 경로 검증 포함)
