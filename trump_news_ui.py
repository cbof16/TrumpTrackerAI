from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
import json

def run_web_ui(get_news_data_func):
    app = Flask(__name__, static_folder="frontend/dist", static_url_path="/")
    CORS(app)
    
    @app.route("/api/news")
    def api_news():
        news = get_news_data_func()
        print("Returning news data:", news)
        return jsonify(news)
    
    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")
    
    return app

def get_news_data():
    """Read news data from JSON file."""
    try:
        with open("trump_news.json", "r") as f:
            news = json.load(f)
        return news
    except FileNotFoundError:
        return [{"title": "Sample News", "summary": "Summary here", "url": "http://example.com", "factCheck": {"status": "Verified", "claims": []}}]

# Ensure the app is accessible at the module level
app = run_web_ui(get_news_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)