#!/usr/bin/env python3
"""
Test run: Scrape, score, summarize, and print sample output.
Does NOT send any emails or publish. Safe to run anytime.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from src.config import PACIFIC, ANTHROPIC_API_KEY
from src.pubmed_scraper import scrape_papers


def main():
    now = datetime.now(PACIFIC)
    brief_date = now + timedelta(days=1)

    print("=== Ortho Minute Test Run ===")
    print(f"Date: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"Brief for: {brief_date.strftime('%A, %B %d')}")
    print()

    # Scrape all journals
    print("--- Scraping PubMed ---")
    papers = scrape_papers()
    print()

    print(f"Total papers found: {len(papers)}")
    for i, p in enumerate(papers[:5]):
        print(f"  {i+1}. {p['title'][:80]}")
        print(f"     {p['journal']} ({p['year']})")
        print(f"     {p['link']}")
    print()

    # Score + summarize if API key is set
    if ANTHROPIC_API_KEY:
        print("--- Scoring + Summarization ---")
        from src.paper_scorer import score_papers
        from src.summarizer import summarize_papers

        if papers:
            ranked = score_papers(papers, top_n=5)
            ranked = summarize_papers(ranked)
            print(f"\nTop {len(ranked)} papers:")
            for i, p in enumerate(ranked):
                print(f"\n  #{i+1} (Score: {p.get('score', 'N/A')})")
                print(f"  {p['title']}")
                print(f"  {p['journal']} ({p['year']})")
                print(f"  {p['link']}")
                for b in p.get("bullets", []):
                    print(f"    - {b}")
    else:
        print("ANTHROPIC_API_KEY not set. Skipping scoring/summarization.")

    print("\n=== Test complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
