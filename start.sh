#!/bin/bash

# Download necessary NLTK data
python -m nltk.downloader punkt stopwords

# Check if we want to run with gunicorn (production) or Flask's development server
if [ -x "$(command -v gunicorn)" ]; then
    echo "Starting server with Gunicorn..."
    # Changed from trump_news_agent:app to trump_news_ui:app
    exec gunicorn --bind 0.0.0.0:5000 trump_news_ui:app
else
    echo "Gunicorn not found, starting with Flask development server..."
    exec python trump_news_agent.py
fi