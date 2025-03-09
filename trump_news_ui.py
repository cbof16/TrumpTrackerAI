from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

def run_web_ui(api_key, get_news_data):
    # Configure the Flask app to serve the frontend built with Vite.
    # Assumes the Vite build is located in the "frontend/dist" directory.
    app = Flask(__name__, static_folder="frontend/dist", static_url_path="/")
    CORS(app)
    
    @app.route("/api/news")
    def api_news():
        # Return the news data as JSON.
        news = get_news_data(api_key)
        print("Returning news data:", news)
        return jsonify(news)
    
    @app.route("/")
    def index():
        # Serve the Vite project's index.html file.
        return send_from_directory(app.static_folder, "index.html")
    
    app.run(host="0.0.0.0", port=5000)