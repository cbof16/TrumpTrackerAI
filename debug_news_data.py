#!/usr/bin/env python3
"""
Utility script to examine the current news data and display statistics.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

def main():
    """Read and analyze the news data JSON file."""
    try:
        with open('trump_news.json', 'r') as f:
            news_data = json.load(f)
    except FileNotFoundError:
        print("Error: trump_news.json file not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: trump_news.json contains invalid JSON.")
        sys.exit(1)
    
    print(f"Total articles: {len(news_data)}")
    
    # Count sources
    sources = Counter(article.get('source', 'Unknown') for article in news_data)
    print("\nSources:")
    for source, count in sources.most_common():
        print(f"  {source}: {count}")
    
    # Count statuses
    statuses = Counter(article.get('factCheck', {}).get('status', 'Unknown') for article in news_data)
    print("\nFact-check statuses:")
    for status, count in statuses.most_common():
        print(f"  {status}: {count}")
    
    # Get date range
    dates = [article.get('publishedAt') for article in news_data if article.get('publishedAt')]
    if dates:
        try:
            parsed_dates = [datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ") for date in dates]
            oldest = min(parsed_dates).strftime("%Y-%m-%d %H:%M:%S")
            newest = max(parsed_dates).strftime("%Y-%m-%d %H:%M:%S")
            print(f"\nDate range: {oldest} to {newest}")
        except ValueError:
            print("\nCouldn't parse dates - format may be inconsistent")
    
    # Display some sample article titles
    print("\nSample article titles:")
    for i, article in enumerate(news_data[:5]):
        print(f"  {i+1}. {article.get('title', 'No title')}")
    
    # Check for missing data
    missing_fields = {
        'title': 0,
        'summary': 0,
        'source': 0,
        'publishedAt': 0,
        'url': 0
    }
    
    for article in news_data:
        for field in missing_fields:
            if not article.get(field):
                missing_fields[field] += 1
    
    print("\nMissing fields:")
    for field, count in missing_fields.items():
        print(f"  {field}: {count}")

if __name__ == "__main__":
    main()
