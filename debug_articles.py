#!/usr/bin/env python3
"""
Debug script to test article fetching and processing.
"""
import json
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger()

# Load environment variables
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    logger.error("NEWS_API_KEY not found in environment")
    sys.exit(1)

def main():
    """Test article fetching with different strategies."""
    from trump_news_agent import fetch_news_with_pagination, filter_articles
    
    # Try with different settings
    for num_articles in [30, 50, 100]:
        logger.info(f"Testing fetch with num_articles={num_articles}")
        articles = fetch_news_with_pagination(NEWS_API_KEY, num_articles=num_articles)
        logger.info(f"Fetched {len(articles)} articles")
        
        filtered = filter_articles(articles)
        logger.info(f"After filtering, have {len(filtered)} articles")
        
        # Save to temp file for inspection
        with open(f"debug_articles_{num_articles}.json", "w") as f:
            json.dump({
                "total_fetched": len(articles),
                "filtered_count": len(filtered),
                "articles": articles,
                "filtered_articles": filtered
            }, f, indent=2)
        logger.info(f"Saved to debug_articles_{num_articles}.json")

if __name__ == "__main__":
    main()
    print("\nDebugging complete. Check the generated JSON files for details.")
    print("You may want to run this script again with different search terms or API settings.")
