"""
패션 아이돌 분석기 - 로컬 서버
실행 방법:
  1. pip install requests flask flask-cors
  2. python server.py
  3. 브라우저에서 http://localhost:5000 접속
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/search')
def search():
    query        = request.args.get('query', '')
    source       = request.args.get('source', 'blog')   # blog | news
    display      = request.args.get('display', '50')
    client_id     = request.args.get('clientId', '')
    client_secret = request.args.get('clientSecret', '')

    if not query or not client_id or not client_secret:
        return jsonify({'error': '파라미터 누락'}), 400

    url = f'https://openapi.naver.com/v1/search/{source}.json'
    headers = {
        'X-Naver-Client-Id': client_id,
        'X-Naver-Client-Secret': client_secret,
    }
    params = {
        'query': query,
        'display': display,
        'sort': 'date',
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'네이버 API 오류: {resp.status_code} - API 키를 확인해주세요'}), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n✅ 서버 시작!")
    print("👉 브라우저에서 http://localhost:5000 열기\n")
    app.run(port=5000, debug=False)
