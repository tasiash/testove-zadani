from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import os
import io
import json
import requests

load_dotenv()

app = Flask(__name__, static_folder="public", static_url_path="")

#GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#CSE_ID = os.getenv("GOOGLE_CSE_ID")

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
PROVIDER = (os.getenv("PROVIDER") or "serpapi").lower()

PORT = int(os.getenv("PORT", "10000"))

# удвление пустого запроса
def validate_query(q):
    if not q or not q.strip():
        return "Empty query"
    return None

#def google_search_first_page(query):
    if not API_KEY or not CSE_ID:
        raise RuntimeError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID in .env")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": 10,
        "start": 1
    }

    r = requests.get(url, params=params, timeout=15)

    # Если ошибка — вернём текст от Google (там причина)
    if not r.ok:
        raise RuntimeError(f"Google API error {r.status_code}: {r.text}")

    data = r.json()

    items = data.get("items") or []
    return [
        {
            "title": it.get("title", ""),
            "url": it.get("link", ""),
            "description": it.get("snippet", "")
        }
        for it in items
    ]

def search_first_page(query: str):
    if PROVIDER != "serpapi":
        raise RuntimeError("Only serpapi provider enabled")

    if not SERPAPI_KEY:
        raise RuntimeError("Missing SERPAPI_KEY in .env")

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 10,
        "start": 0,
    }

    r = requests.get(url, params=params, timeout=20)

    if not r.ok:
        raise RuntimeError(f"SerpApi error {r.status_code}: {r.text}")

    data = r.json()
    organic = data.get("organic_results") or []

    return [
        {
            "title": it.get("title", ""),
            "url": it.get("link", ""),
            "description": it.get("snippet", ""),
        }
        for it in organic[:1]
    ]
@app.get("/")
def home():
    return app.send_static_file("index.html")

@app.get("/api/search")
def api_search():
    q = request.args.get("q")
    err = validate_query(q)
    if err:
        return jsonify({"error": err}), 400

    try:
        results = search_first_page(q.strip())
        return jsonify({"query": q.strip(), "results": results})
    except Exception as e:
        return jsonify({"error": "Search failed", "details": str(e)}), 500

@app.get("/api/export")
def api_export():
    q = request.args.get("q")
    err = validate_query(q)
    if err:
        return jsonify({"error": err}), 400

    try:
        results = search_first_page(q.strip())
        payload = {"query": q.strip(), "results": results}

        buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/json",
            as_attachment=True,
            download_name="results.json"
        )
    except Exception as e:
        return jsonify({"error": "Export failed", "details": str(e)}), 500

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=PORT, debug=True)
