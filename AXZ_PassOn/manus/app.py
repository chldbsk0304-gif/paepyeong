from __future__ import annotations
import os
import shutil
from flask import Flask, render_template, request, redirect, url_for
import sys

# 상위 디렉토리의 config를 가져오기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DIRS

app = Flask(__name__, static_folder=os.path.dirname(DIRS["temp"]))

@app.route('/')
def index():
    # temp 폴더의 이미지 목록 가져오기
    images = [f for f in os.listdir(DIRS["temp"]) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return render_template('index.html', images=images)

@app.route('/select', methods=['POST'])
def select():
    selected_images = request.form.getlist('images')
    for img in selected_images:
        src = os.path.join(DIRS["temp"], img)
        dst = os.path.join(DIRS["images"], img)
        shutil.move(src, dst)
        if os.path.exists(dst):
            print(f"[SUCCESS] Image moved to final folder: {dst}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # index.html 템플릿 생성 로직 (간소화)
    os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "templates/index.html"), "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head><title>Image Selector</title></head>
        <body>
            <h1>Select Images to Save</h1>
            <form action="/select" method="post">
                {% for img in images %}
                <div>
                    <img src="/static/temp/{{ img }}" width="200">
                    <input type="checkbox" name="images" value="{{ img }}">
                </div>
                {% endfor %}
                <button type="submit">Move Selected to Images Folder</button>
            </form>
        </body>
        </html>
        """)
    app.run(port=5000, debug=True)
