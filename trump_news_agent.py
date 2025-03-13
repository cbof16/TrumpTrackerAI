#!/usr/bin/env python3
import os
import json
import logging
import threading
import time
import schedule
from dotenv import load_dotenv
load_dotenv()

import requests
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
import heapq
import nltk

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
        "pageSize": 30
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
    """Query an external fact-checking API for a given claim."""
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
        logging.info(f"Sending fact check request for: '{claim[:50]}...'")
        response = requests.get(api_url, params=params)
        if response.status_code == 403:
            logging.error(f"Access forbidden (403) for claim; check API key.")
            return {}
        response.raise_for_status()
        result = response.json()
        if result.get("claims"):
            logging.info(f"Found {len(result.get('claims'))} claims for: '{claim[:50]}...'")
        else:
            logging.info(f"No claims found for: '{claim[:50]}...'")
        return result
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying fact-check API: {e}")
        return {}


def improved_fact_check_article(article, fact_check_api_key: str):
    """Extract claims and return fact-check results with source details."""
    title = article.get("title", "")
    description = article.get("description", "") or ""
    content = article.get("content", "") or ""
    url = article.get("url", "")
    
    # Check if the article itself is from a fact-checking source or about fact-checking
    fact_check_sources = ["factcheck.org", "politifact", "snopes", "fact-check", "factcheck"]
    is_fact_check_source = any(source in url.lower() for source in fact_check_sources)
    is_about_fact_checking = "fact" in title.lower() and "check" in title.lower()
    
    text = description + " " + content
    if not text.strip():
        return {"status": "Insufficient content", "claims": []}
    
    claims_sentences = sent_tokenize(text)
    disputed_claims = []
    
    # If it's a fact-checking article itself, extract potential claims
    if is_fact_check_source or is_about_fact_checking:
        logging.info(f"Article appears to be a fact-checking article: {title}")
        # Extract at least one claim from the article itself
        if "Trump" in title:
            disputed_claims.append({
                "claim": title,
                "publisher": article.get("source", {}).get("name", "Article Source"),
                "url": url
            })
    
    # Try to find claims via API for relevant sentences
    relevant_sentences = [s for s in claims_sentences if "Trump" in s]
    for claim in relevant_sentences[:3]:  # Limit to first 3 relevant sentences to avoid API overuse
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
    
    # If still no claims but it's a fact-checking article, add a generic claim
    if not disputed_claims and (is_fact_check_source or is_about_fact_checking):
        disputed_claims.append({
            "claim": f"This article from {article.get('source', {}).get('name', 'Unknown')} fact-checks statements related to Trump",
            "publisher": article.get("source", {}).get("name", "Article Source"),
            "url": url
        })
    
    status = "Disputed" if disputed_claims else "Verified"
    return {"status": status, "claims": disputed_claims}


def run_trump_news_agent(news_api_key: str, fact_check_api_key: str):
    """Fetch, process, and save news articles to a JSON file."""
    logging.info("Fetching news articles...")
    articles = fetch_news(news_api_key)
    if not articles:
        logging.error("No articles fetched. Using fallback data.")
        fallback = [{
            "title": "Sample News",
            "summary": "This is sample news from backend",
            "publishedAt": "N/A",
            "source": "Backend",
            "url": "#",
            "factCheck": {"status": "Verified", "claims": []}
        }]
        with open("trump_news.json", "w") as f:
            json.dump(fallback, f, indent=4)
        logging.info("Saved fallback data to trump_news.json")
        return
    
    filtered_articles = filter_articles(articles)
    logging.info("Generating summaries and performing fact-checking...")
    
    news_data = []
    for article in filtered_articles:
        summary = summarize_article(article)
        fact_check = improved_fact_check_article(article, fact_check_api_key)
        news_data.append({
            "title": article.get("title", "No Title"),
            "summary": summary,
            "publishedAt": article.get("publishedAt", "N/A"),
            "source": article.get("source", {}).get("name", "Unknown"),
            "url": article.get("url", "#"),
            "factCheck": fact_check
        })
    with open("trump_news.json", "w") as f:
        json.dump(news_data, f, indent=4)
    logging.info("Saved news data to trump_news.json")

def get_news_data():
    """Read cached news data from file for UI consumption."""
    try:
        with open("trump_news.json", "r") as f:
            news_data = json.load(f)
        logging.info("Loaded news data from trump_news.json")
        return news_data
    except (FileNotFoundError, json.JSONDecodeError):
        fallback = [{
            "title": "Sample News",
            "summary": "This is sample news from backend",
            "publishedAt": "N/A",
            "source": "Backend",
            "url": "#",
            "factCheck": {"status": "Verified", "claims": []}
        }]
        logging.warning("Error loading trump_news.json, returning fallback data")
        return fallback

def run_scheduled_updates(news_api_key: str, fact_check_api_key: str):
    """Run scheduled updates every 30 minutes."""
    schedule.every(30).minutes.do(lambda: run_trump_news_agent(news_api_key, fact_check_api_key))
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Initial run to populate the JSON file
    run_trump_news_agent(NEWS_API_KEY, FACT_CHECK_API_KEY)
    
    # Start scheduled updates in a separate thread
    updater_thread = threading.Thread(
        target=run_scheduled_updates,
        args=(NEWS_API_KEY, FACT_CHECK_API_KEY),
        daemon=True
    )
    updater_thread.start()
    
    # Start the web UI
    logging.info("Starting web UI on port 5000.")
    from trump_news_ui import run_web_ui
    run_web_ui(get_news_data)  # Pass the no-argument function