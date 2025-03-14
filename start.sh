#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Create necessary directories
echo "Setting up directories..."
mkdir -p frontend/dist

# Set proper permissions
chmod -R 755 frontend

# Download necessary NLTK data
echo "Downloading NLTK data..."
python -m nltk.downloader punkt stopwords

# Make sure we have a trump_news.json file
echo "Checking for news data..."
if [ ! -f trump_news.json ]; then
    echo "Creating sample trump_news.json..."
    echo '[{"title":"Sample News","summary":"This is sample news from start.sh","publishedAt":"2023-01-01T12:00:00Z","source":"Sample","url":"#","factCheck":{"status":"Verified","claims":[]}}]' > trump_news.json
fi

# Check if the index.html file exists and has content
echo "Checking frontend files..."
if [ ! -s frontend/dist/index.html ]; then
    echo "Creating index.html..."
    # Create a minimal version that will be replaced by the proper version from trump_news_ui.py
    echo '<!DOCTYPE html><html><head><title>Loading...</title></head><body><p>Loading UI...</p></body></html>' > frontend/dist/index.html
fi

# Print environment variables for debugging (without values for security)
echo "Checking environment variables..."
if [ -z "$NEWS_API_KEY" ]; then
    echo "WARNING: NEWS_API_KEY is not set"
else
    echo "NEWS_API_KEY is set"
fi

if [ -z "$FACT_CHECK_API_KEY" ]; then
    echo "WARNING: FACT_CHECK_API_KEY is not set"
else
    echo "FACT_CHECK_API_KEY is set"
fi

# Check if we want to run with gunicorn (production) or Flask's development server
if [ -x "$(command -v gunicorn)" ]; then
    echo "Starting server with Gunicorn..."
    exec gunicorn --bind 0.0.0.0:5000 --log-level debug trump_news_ui:app
else
    echo "Gunicorn not found, starting with Flask development server..."
    exec python trump_news_ui.py
fi