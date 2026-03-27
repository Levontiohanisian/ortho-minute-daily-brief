#!/usr/bin/env python3
"""
Test run: Scrape, score, summarize, and print sample output.
Does NOT send any emails or publish. Safe to run anytime.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from src.config import (
    PACIFIC,
    DATA_DIR,
    get_today_subspecialty,
    get_second_slot,
    ANTHROPIC_API_KEY,
)
from src.pubmed_scraper import scrape_papers


def main():
    now = datetime.now(PACIFIC)
    brief_date = now + timedelta(days=1)

    print("=== Ortho Minute Test Run ===")
    print(f"Date: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print()

    slot1 = get_today_subspecialty(brief_date)
    slot2 = get_second_slot(brief_date)

    print(f"Tomorrow's slot 1: {slot1}")
    print(f"Tomorrow's slot 2: {slot2}")
    print()

    # Test PubMed scraping
    print("--- Testing PubMed Scrape ---")
    slot1_papers = scrape_papers(slot1)
    slot2_papers = scrape_papers(slot2)
    print()

    print(f"Slot 1 ({slot1}) papers found: {len(slot1_papers)}")
    for i, p in enumerate(slot1_papers[:3]):
        print(f"  {i+1}. {p['title'][:80]}")
        print(f"     {p['journal']} ({p['year']})")
        print(f"     {p['link']}")
    print()

    print(f"Slot 2 ({slot2}) papers found: {len(slot2_papers)}")
    for i, p in enumerate(slot2_papers[:3]):
        print(f"  {i+1}. {p['title'][:80]}")
        print(f"     {p['journal']} ({p['year']})")
        print(f"     {p['link']}")
    print()

    # Test scoring + summarization if API key is set
    if ANTHROPIC_API_KEY:
        print("--- Testing Scoring + Summarization ---")
        from src.paper_scorer import score_papers
        from src.summarizer import summarize_papers

        if slot1_papers:
            ranked = score_papers(slot1_papers, slot1, top_n=3)
            ranked = summarize_papers(ranked)
            print(f"\nTop {len(ranked)} {slot1} papers:")
            for i, p in enumerate(ranked):
                print(f"\n  #{i+1} (Score: {p.get('score', 'N/A')})")
                print(f"  {p['title']}")
                print(f"  {p['journal']} ({p['year']})")
                print(f"  {p['link']}")
                for b in p.get("bullets", []):
                    print(f"    - {b}")

        if slot2_papers:
            ranked = score_papers(slot2_papers, slot2, top_n=3)
            ranked = summarize_papers(ranked)
            print(f"\nTop {len(ranked)} {slot2} papers:")
            for i, p in enumerate(ranked):
                print(f"\n  #{i+1} (Score: {p.get('score', 'N/A')})")
                print(f"  {p['title']}")
                print(f"  {p['journal']} ({p['year']})")
                print(f"  {p['link']}")
                for b in p.get("bullets", []):
                    print(f"    - {b}")
    else:
        print("ANTHROPIC_API_KEY not set. Skipping scoring/summarization test.")
        print("Set it with: export ANTHROPIC_API_KEY=your_key_here")

    print("\n=== Test complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
