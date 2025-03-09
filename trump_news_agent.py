#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv
load_dotenv()

import requests
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
import heapq
import nltk
import threading
import time
import schedule

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load API keys from environment variables
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FACT_CHECK_API_KEY = os.getenv("FACT_CHECK_API_KEY")

# Ensure required NLTK data is available
for resource in ['tokenizers/punkt', 'corpora/stopwords']:
    try:
        nltk.data.find(resource)
    except LookupError:
        nltk.download(resource.split('/')[1])

def fetch_news(api_key: str):
    """Fetch news articles using the NewsAPI."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "Donald Trump",
        "apiKey": api_key,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 10
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        logging.info(f"Fetched {len(articles)} articles.")
        return articles
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news: {e}")
        return []

def filter_articles(articles):
    """Filter articles to ensure they contain relevant keywords."""
    keywords = ["Trump", "Donald Trump"]
    filtered = []
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        content = (title + " " + description).lower()
        if any(keyword.lower() in content for keyword in keywords):
            filtered.append(article)
    logging.info(f"Filtered {len(filtered)} relevant articles.")
    return filtered

def summarize_article(article, num_sentences=2):
    """Generate a summary for an article using extractive summarization."""
    text = article.get("description") or article.get("content") or article.get("title", "")
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return " ".join(sentences)
    
    stop_words = set(stopwords.words("english"))
    word_freq = defaultdict(int)
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word.isalnum() and word not in stop_words:
                word_freq[word] += 1
                
    sentence_scores = defaultdict(int)
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                sentence_scores[sentence] += word_freq[word]
    
    summary_sentences = heapq.nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    return " ".join(summary_sentences)

def query_fact_check(claim: str, fact_check_api_key: str):
    """
    Query an external fact-checking API for a given claim.
    If the fact-check API key is not configured, skip the query.
    """
    if fact_check_api_key in [None, "", "your_fact_check_api_key_here"]:
        logging.warning(f"Fact-check API key not configured; skipping fact check for claim: '{claim}'")
        return {}
    api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": claim,
        "key": fact_check_api_key,
        "languageCode": "en"
    }
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 403:
            logging.error(f"Access forbidden (403) when querying fact-check API for claim '{claim}'; check your API key and permissions.")
            return {}
        response.raise_for_status()
        logging.info(f"Successfully fetched fact-check result for claim: '{claim}'")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying fact-check API for claim '{claim}': {e}")
        return {}

def improved_fact_check_article(article, fact_check_api_key: str):
    """
    Extract sentences from the article as potential claims, query the fact-check API,
    and return a structured result with a status and a list of disputed claims including source details.
    """
    text = (article.get("description") or "") + " " + (article.get("content") or "")
    if not text.strip():
        return {"status": "Insufficient content", "claims": []}
    
    claims_sentences = sent_tokenize(text)
    disputed_claims = []
    
    for claim in claims_sentences:
        result = query_fact_check(claim, fact_check_api_key)
        if result and result.get("claims"):
            for fact in result["claims"]:
                reviews = fact.get("claimReview", [])
                for review in reviews:
                    disputed_claims.append({
                        "claim": claim,
                        "publisher": review.get("publisher", {}).get("name", "Unknown Source"),
                        "url": review.get("url", "#")
                    })
    status = "Disputed" if disputed_claims else "Verified"
    return {"status": status, "claims": disputed_claims}

def run_trump_news_agent(news_api_key: str, fact_check_api_key: str):
    """Fetch, filter, summarize, and fact-check news articles."""
    logging.info("Fetching news articles...")
    articles = fetch_news(news_api_key)
    if not articles:
        logging.error("No articles fetched. Exiting.")
        return
    filtered_articles = filter_articles(articles)
    logging.info("Generating summaries and performing improved fact-checking...")
    
    for idx, article in enumerate(filtered_articles, 1):
        summary = summarize_article(article)
        fact_check = improved_fact_check_article(article, fact_check_api_key)
        logging.info(f"\nArticle {idx}: {article.get('title')}\nSummary: {summary}\nFact-check: {fact_check}")

def get_news_data(news_api_key: str, fact_check_api_key: str):
    """Retrieve news data and return structured articles for UI consumption."""
    articles = fetch_news(news_api_key)
    if not articles:
        fallback = [{
            "title": "Sample News",
            "summary": "This is sample news from backend",
            "factCheck": {"status": "Verified", "claims": []}
        }]
        logging.warning(f"No articles fetched, returning fallback data: {fallback}")
        return fallback
    
    filtered_articles = filter_articles(articles)
    news_data = []
    for article in filtered_articles:
        title = article.get("title", "No Title")
        summary = summarize_article(article)
        fact_check = improved_fact_check_article(article, fact_check_api_key)
        news_data.append({"title": title, "summary": summary, "factCheck": fact_check})
    logging.info(f"Returning actual news data: {news_data}")
    return news_data

def run_scheduled_updates(news_api_key: str, fact_check_api_key: str):
    """Run scheduled updates to fetch and process news every 30 minutes."""
    schedule.every(30).minutes.do(lambda: run_trump_news_agent(news_api_key, fact_check_api_key))
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Initial run of the agent (console output)
    run_trump_news_agent(NEWS_API_KEY, FACT_CHECK_API_KEY)
    
    # Start scheduled updates in a separate thread
    updater_thread = threading.Thread(target=run_scheduled_updates, args=(NEWS_API_KEY, FACT_CHECK_API_KEY), daemon=True)
    updater_thread.start()
    
    # Start the web UI to display news (assumes trump_news_ui.py exists and supports the new signature)
    logging.info("Starting web UI on port 5000.")
    from trump_news_ui import run_web_ui
    run_web_ui(NEWS_API_KEY, lambda: get_news_data(NEWS_API_KEY, FACT_CHECK_API_KEY))
