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
    get_arthroplasty_slot,
    ANTHROPIC_API_KEY,
)
from src.pubmed_scraper import scrape_papers


def main():
    now = datetime.now(PACIFIC)
    brief_date = now + timedelta(days=1)

    print("=== Ortho Minute Test Run ===")
    print(f"Date: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print()

    subspecialty = get_today_subspecialty(brief_date)
    arthroplasty_slot = get_arthroplasty_slot(brief_date)

    if subspecialty == arthroplasty_slot:
        arthroplasty_slot = (
            "Total Knee Arthroplasty"
            if arthroplasty_slot == "Total Hip Arthroplasty"
            else "Total Hip Arthroplasty"
        )

    print(f"Tomorrow's subspecialty: {subspecialty}")
    print(f"Arthroplasty slot: {arthroplasty_slot}")
    print()

    # Test PubMed scraping
    print("--- Testing PubMed Scrape ---")
    subspec_papers = scrape_papers(subspecialty)
    arthro_papers = scrape_papers(arthroplasty_slot)
    print()

    print(f"Subspecialty papers found: {len(subspec_papers)}")
    for i, p in enumerate(subspec_papers[:3]):
        print(f"  {i+1}. {p['title'][:80]}")
        print(f"     {p['journal']} ({p['year']})")
    print()

    print(f"Arthroplasty papers found: {len(arthro_papers)}")
    for i, p in enumerate(arthro_papers[:3]):
        print(f"  {i+1}. {p['title'][:80]}")
        print(f"     {p['journal']} ({p['year']})")
    print()

    # Test scoring + summarization if API key is set
    if ANTHROPIC_API_KEY:
        print("--- Testing Scoring + Summarization ---")
        from src.paper_scorer import score_papers
        from src.summarizer import summarize_papers

        if subspec_papers:
            ranked = score_papers(subspec_papers, subspecialty, top_n=3)
            ranked = summarize_papers(ranked)
            print(f"\nTop {len(ranked)} {subspecialty} papers:")
            for i, p in enumerate(ranked):
                print(f"\n  #{i+1} (Score: {p.get('score', 'N/A')})")
                print(f"  {p['title']}")
                print(f"  {p['journal']} ({p['year']})")
                for b in p.get("bullets", []):
                    print(f"    - {b}")

        if arthro_papers:
            ranked = score_papers(arthro_papers, arthroplasty_slot, top_n=3)
            ranked = summarize_papers(ranked)
            print(f"\nTop {len(ranked)} {arthroplasty_slot} papers:")
            for i, p in enumerate(ranked):
                print(f"\n  #{i+1} (Score: {p.get('score', 'N/A')})")
                print(f"  {p['title']}")
                print(f"  {p['journal']} ({p['year']})")
                for b in p.get("bullets", []):
                    print(f"    - {b}")
    else:
        print("ANTHROPIC_API_KEY not set. Skipping scoring/summarization test.")
        print("Set it with: export ANTHROPIC_API_KEY=your_key_here")

    print("\n=== Test complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
