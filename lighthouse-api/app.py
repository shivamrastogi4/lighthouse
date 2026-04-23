import requests
import time
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


def run_lighthouse(url, retries=3):
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    params = [
        ("url", url),
        ("key", GOOGLE_API_KEY),
        ("strategy", mode),
        ("category", "performance"),
        ("category", "accessibility"),
        ("category", "best-practices"),
        ("category", "seo"),
    ]

    for attempt in range(retries):
        try:
            response = requests.get(api_url, params=params, timeout=(10, 60))
            if response.status_code == 200:
                data = response.json()
                lighthouse = data.get("lighthouseResult", {})
                categories = lighthouse.get("categories", {})

                return {
                    "performance": categories.get("performance", {}).get("score", 0) * 100,
                    "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
                    "best_practices": categories.get("best-practices", {}).get("score", 0) * 100,
                    "seo": categories.get("seo", {}).get("score", 0) * 100
                }

        except requests.exceptions.Timeout:
            time.sleep(2 ** attempt)

    return {"error": "Lighthouse API timed out"}


def check_website(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        end = time.time()

        return {
            "status": response.status_code,
            "response_time": round(end - start, 2)
        }

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@app.route("/")
def home():
    return "Lighthouse API is running 🚀"


@app.route("/lighthouse", methods=["GET"])
def lighthouse_api():
    url = request.args.get("url")
    mode = request.args.get("mode", "mobile").lower()
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    if mode not in ["mobile", "desktop"]:
        return jsonify({
            "error": "Invalid mode. Use 'mobile' or 'desktop'"
        }), 400


    if not url.startswith("http"):
        url = "https://" + url
    lighthouse_result = run_lighthouse(url,mode)
    website_status = check_website(url)

    if "error" in lighthouse_result:
        return jsonify(lighthouse_result), 500

    return jsonify({
        "url": url,
        "mode": mode,
        "status": website_status,
        "lighthouse": lighthouse_result,
        "note": "Defaulted to mobile" if "mode" not in request.args else ""
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
