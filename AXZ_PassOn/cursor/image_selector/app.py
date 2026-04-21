# -*- coding: utf-8 -*-
"""이미지 선택기 Flask 앱: temp 이미지 표시 → 선택 이미지를 images로 이동 (Python 3.9 호환)."""
from __future__ import annotations

import os
import shutil
from typing import List

from flask import Flask, jsonify, request, send_from_directory

# 프로젝트 루트에서 config 로드 (실행 시 루트가 cwd여야 함)
import sys
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import BASE_PATH, IMAGES_DIR, TEMP_DIR, ensure_dirs

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

# 허용 이미지 확장자
ALLOWED_EXT = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp"})


def _list_temp_images() -> List[str]:
    """temp 폴더 내 이미지 파일명 목록 (절대경로 기준)."""
    ensure_dirs()
    if not os.path.isdir(TEMP_DIR):
        return []
    out: List[str] = []
    for name in os.listdir(TEMP_DIR):
        if os.path.splitext(name)[1].lower() in ALLOWED_EXT:
            out.append(name)
    return sorted(out)


@app.route("/")
def index() -> str:
    """temp 이미지 목록을 보여주는 간단한 HTML."""
    images = _list_temp_images()
    rows = "".join(
        f'<li data-filename="{n}">'
        f'<img src="/temp/{n}" alt="{n}" style="max-width:200px;max-height:200px;"> '
        f'<label><input type="checkbox" name="select" value="{n}"> 선택</label>'
        f"</li>"
        for n in images
    )
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>디지털 옷장 - 이미지 선택</title></head>
<body>
  <h1>옷 이미지 선택 (앞/뒷면 등 저장할 사진을 고른 뒤 저장)</h1>
  <ul id="list">{rows if rows else "<li>temp 폴더에 이미지가 없습니다.</li>"}</ul>
  <p><button id="save">선택한 이미지를 옷장(images)에 저장</button></p>
  <p id="msg"></p>
  <script>
    document.getElementById('save').onclick = function() {{
      var names = Array.from(document.querySelectorAll('input[name=select]:checked')).map(function(c) {{ return c.value; }});
      if (!names.length) {{ document.getElementById('msg').textContent = '한 개 이상 선택해주세요.'; return; }}
      fetch('/save', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ filenames: names }}) }})
        .then(function(r) {{ return r.json(); }})
        .then(function(d) {{ document.getElementById('msg').textContent = d.message || d.error || '완료'; }})
        .catch(function(e) {{ document.getElementById('msg').textContent = '오류: ' + e; }});
    }};
  </script>
</body>
</html>
"""


@app.route("/temp/<path:filename>")
def serve_temp(filename: str) -> "flask.Response":
    """temp 디렉터리 이미지 서빙."""
    dir_ = os.path.abspath(TEMP_DIR)
    return send_from_directory(dir_, filename)


@app.route("/api/list")
def api_list() -> "flask.Response":
    """temp 이미지 목록 JSON."""
    return jsonify({"filenames": _list_temp_images()})


@app.route("/save", methods=["POST"])
def save() -> "flask.Response":
    """선택한 이미지를 temp → AXZ_PassOn/images로 shutil.move 후 경로 검증."""
    ensure_dirs()
    data = request.get_json(force=True, silent=True) or {}
    filenames: List[str] = data.get("filenames") or []
    if not filenames:
        return jsonify({"ok": False, "error": "filenames 없음"}), 400

    # 경로 검증: IMAGES_DIR이 정확히 AXZ_PassOn/images인지 확인
    expected_images_dir = os.path.join(BASE_PATH, "images")
    if not os.path.abspath(IMAGES_DIR) == os.path.abspath(expected_images_dir):
        return jsonify({
            "ok": False,
            "error": f"경로 불일치: IMAGES_DIR={IMAGES_DIR}, 예상={expected_images_dir}"
        }), 500

    moved: List[str] = []
    errors: List[str] = []
    for name in filenames:
        if ".." in name or "/" in name or "\\" in name:
            errors.append(f"잘못된 파일명: {name}")
            continue
        src = os.path.join(TEMP_DIR, name)
        if not os.path.isfile(src):
            errors.append(f"파일 없음: {name}")
            continue
        dst = os.path.join(IMAGES_DIR, name)
        # 최종 목적지 경로가 AXZ_PassOn/images 내부인지 검증
        if not os.path.abspath(dst).startswith(os.path.abspath(expected_images_dir)):
            errors.append(f"경로 검증 실패: {dst}가 {expected_images_dir} 내부가 아님")
            continue
        try:
            shutil.move(src, dst)
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue
        # 저장 후 하드디스크 기록 검증
        if os.path.exists(dst) and os.path.abspath(dst).startswith(os.path.abspath(expected_images_dir)):
            moved.append(dst)
        else:
            errors.append(f"저장 후 검증 실패: {name} (경로={dst})")

    if not moved and errors:
        return jsonify({"ok": False, "error": "; ".join(errors)}), 500
    msg = f"저장 완료: {len(moved)}개 → {expected_images_dir} (하드디스크 기록 검증됨)"
    if errors:
        msg += " 오류: " + "; ".join(errors)
    return jsonify({"ok": True, "message": msg, "saved_count": len(moved), "saved_paths": moved, "target_dir": expected_images_dir})


if __name__ == "__main__":
    ensure_dirs()
    app.run(host="127.0.0.1", port=5000, debug=True)
