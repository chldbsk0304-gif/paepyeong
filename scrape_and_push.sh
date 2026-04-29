#!/usr/bin/env bash
# 무신사 스크래퍼 실행 → 중복 제거 → dummyProducts.js 변경 시 자동 GitHub push
#
# 사용법:
#   ./scrape_and_push.sh          # 신규 스크래핑 + 중복 제거 + push
#   ./scrape_and_push.sh --clean  # 기존 파일 중복 제거만 + push (재스크래핑 없음)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUMMY_FILE="src/data/dummyProducts.js"
BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD)"
CLEAN_ONLY="${1:-}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ "$CLEAN_ONLY" == "--clean" ]]; then
  echo "  패평 · 중복 제거 + 자동 push"
else
  echo "  패평 · 무신사 스크래퍼 + 자동 push"
fi
echo "  브랜치: $BRANCH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$SCRIPT_DIR"

# ── 1. 스크래퍼 실행 (또는 --clean 모드) ──────
echo ""
if [[ "$CLEAN_ONLY" == "--clean" ]]; then
  echo "▶ [1/3] 기존 파일 중복 제거 중..."
  python3 musinsa_scraper.py --clean
  echo "✅ 중복 제거 완료"
else
  echo "▶ [1/3] 스크래퍼 실행 중... (중복 자동 제거 포함)"
  python3 musinsa_scraper.py
  echo "✅ 스크래퍼 + 중복 제거 완료"
fi

# ── 2. 변경 감지 ──────────────────────────────
echo ""
echo "▶ [2/3] 변경 사항 확인 중..."

if git -C "$SCRIPT_DIR" diff --quiet -- "$DUMMY_FILE" && \
   ! git -C "$SCRIPT_DIR" ls-files --others --exclude-standard -- "$DUMMY_FILE" | grep -q .; then
  echo "ℹ️  $DUMMY_FILE 변경 없음 — push 생략"
  exit 0
fi

ADDED=$(git -C "$SCRIPT_DIR" diff --stat -- "$DUMMY_FILE" | grep -oP '\d+(?= insertion)' || echo 0)
REMOVED=$(git -C "$SCRIPT_DIR" diff --stat -- "$DUMMY_FILE" | grep -oP '\d+(?= deletion)' || echo 0)
echo "✅ 변경 감지: +${ADDED} / -${REMOVED} lines"

# ── 3. 커밋 + push ────────────────────────────
echo ""
echo "▶ [3/3] GitHub push 중..."

TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"
if [[ "$CLEAN_ONLY" == "--clean" ]]; then
  MSG="chore: dummyProducts 중복 제거 ($TIMESTAMP)"
else
  MSG="chore: 무신사 랭킹 데이터 업데이트 ($TIMESTAMP)"
fi

git -C "$SCRIPT_DIR" add "$DUMMY_FILE"
git -C "$SCRIPT_DIR" commit -m "$MSG"
git -C "$SCRIPT_DIR" push origin "$BRANCH"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 완료! $DUMMY_FILE → $BRANCH push됨"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
