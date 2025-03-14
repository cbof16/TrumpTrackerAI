from flask import Flask, send_from_directory, jsonify, request, make_response
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_web_ui(get_news_data_func):
    # Ensure the frontend directory exists
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
    os.makedirs(frontend_dir, exist_ok=True)
    
    # Check if index.html exists, if not create a basic one
    index_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_path):
        logger.warning(f"index.html not found at {index_path}, creating basic version")
        with open(index_path, "w") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>TrumpTracker AI</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1 class="text-center">TrumpTracker AI</h1>
        <div id="news-container" class="row mt-4">Loading...</div>
    </div>
    <script>
        fetch('/api/news')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('news-container');
                container.innerHTML = '';
                data.forEach(item => {
                    container.innerHTML += `<div class="col-md-4 mb-3">
                        <div class="card">
                            <div class="card-body">
                                <h5>${item.title}</h5>
                                <p>${item.summary}</p>
                                <a href="${item.url}" target="_blank" class="btn btn-primary">Read More</a>
                            </div>
                        </div>
                    </div>`;
                });
            });
    </script>
</body>
</html>
            """)
    
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    CORS(app)
    
    @app.route("/api/news")
    def api_news():
        news = get_news_data_func()
        logger.info(f"API request received, returning {len(news)} news items")
        
        # Add debug headers to response
        response = make_response(jsonify(news))
        response.headers['X-Article-Count'] = str(len(news))
        response.headers['X-Trump-Tracker-Version'] = '1.1'
        response.headers['X-Expected-Count'] = '30'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route("/api/debug")
    def api_debug():
        """Endpoint to get debugging information about the news data."""
        news = get_news_data_func()
        debug_info = {
            "article_count": len(news),
            "sources": list(set(article.get("source", "Unknown") for article in news)),
            "statuses": {},
            "timestamps": {
                "oldest": min((article.get("publishedAt", "N/A") for article in news), default="N/A"),
                "newest": max((article.get("publishedAt", "N/A") for article in news), default="N/A")
            }
        }
        
        # Count articles by status
        for article in news:
            status = article.get("factCheck", {}).get("status", "Unknown")
            debug_info["statuses"][status] = debug_info["statuses"].get(status, 0) + 1
        
        logger.info(f"Debug info requested: {debug_info}")
        return jsonify(debug_info)
    
    @app.route("/")
    def index():
        logger.info(f"Serving index.html from {app.static_folder}")
        return send_from_directory(app.static_folder, "index.html")
    
    @app.route("/<path:path>")
    def serve_static(path):
        logger.info(f"Serving static file: {path}")
        return send_from_directory(app.static_folder, path)
    
    # Add an error handler for more informative errors
    @app.errorhandler(404)
    def page_not_found(e):
        logger.error(f"404 error: {e}")
        return jsonify(error="Resource not found", path=request.path), 404
    
    return app

def get_news_data():
    """Read news data from JSON file."""
    try:
        with open("trump_news.json", "r") as f:
            news = json.load(f)
        logger.info(f"Successfully loaded {len(news)} news items from trump_news.json")
        return news
    except FileNotFoundError:
        logger.warning("trump_news.json not found, returning sample data")
        return [{"title": "Sample News", "summary": "Summary here", "url": "http://example.com", "factCheck": {"status": "Verified", "claims": []}}]
    except json.JSONDecodeError:
        logger.error("Error decoding trump_news.json, returning sample data")
        return [{"title": "Sample News", "summary": "JSON decode error occurred", "url": "http://example.com", "factCheck": {"status": "Verified", "claims": []}}]

# Ensure the app is accessible at the module level
app = run_web_ui(get_news_data)

if __name__ == "__main__":
    logger.info("Starting Flask development server on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)