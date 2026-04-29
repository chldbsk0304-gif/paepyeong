#!/usr/bin/env bash
# 무신사 스크래퍼 실행 → dummyProducts.js 변경 시 자동 GitHub push
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUMMY_FILE="src/data/dummyProducts.js"
BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  패평 · 무신사 스크래퍼 + 자동 push"
echo "  브랜치: $BRANCH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. 스크래퍼 실행 ──────────────────────────
echo ""
echo "▶ [1/3] 스크래퍼 실행 중..."
cd "$SCRIPT_DIR"
python3 musinsa_scraper.py
echo "✅ 스크래퍼 완료"

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
git -C "$SCRIPT_DIR" add "$DUMMY_FILE"
git -C "$SCRIPT_DIR" commit -m "chore: 무신사 랭킹 데이터 업데이트 ($TIMESTAMP)"
git -C "$SCRIPT_DIR" push origin "$BRANCH"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 완료! $DUMMY_FILE → $BRANCH push됨"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
