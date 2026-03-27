#!/usr/bin/env python3
"""
Evening pipeline: Scrape, score, summarize, save candidates, send preview.
Runs at 7pm Pacific daily via GitHub Actions.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.config import (
    PACIFIC,
    DATA_DIR,
    get_today_subspecialty,
    get_arthroplasty_slot,
)
from src.pubmed_scraper import scrape_papers
from src.paper_scorer import score_papers
from src.summarizer import summarize_papers
from src.preview_email import send_preview_email


def main():
    now = datetime.now(PACIFIC)
    # The brief date is tomorrow (papers found tonight, brief sent tomorrow morning)
    brief_date = now + timedelta(days=1)

    print(f"=== Ortho Minute Evening Pipeline ===")
    print(f"Running at: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"Brief date: {brief_date.strftime('%A, %B %d, %Y')}")

    subspecialty = get_today_subspecialty(brief_date)
    arthroplasty_slot = get_arthroplasty_slot(brief_date)

    # If subspecialty is the same as arthroplasty slot, adjust
    if subspecialty == arthroplasty_slot:
        arthroplasty_slot = (
            "Total Knee Arthroplasty"
            if arthroplasty_slot == "Total Hip Arthroplasty"
            else "Total Hip Arthroplasty"
        )

    print(f"Subspecialty: {subspecialty}")
    print(f"Arthroplasty slot: {arthroplasty_slot}")
    print()

    # Step 1: Scrape papers for both slots
    print("--- Step 1: Scraping PubMed ---")
    subspec_papers = scrape_papers(subspecialty)
    arthro_papers = scrape_papers(arthroplasty_slot)
    print()

    if not subspec_papers:
        print(f"WARNING: No papers found for {subspecialty}")
    if not arthro_papers:
        print(f"WARNING: No papers found for {arthroplasty_slot}")

    # Step 2: Score papers
    print("--- Step 2: Scoring papers ---")
    subspec_ranked = score_papers(subspec_papers, subspecialty, top_n=5)
    arthro_ranked = score_papers(arthro_papers, arthroplasty_slot, top_n=5)
    print(f"  Subspecialty candidates: {len(subspec_ranked)}")
    print(f"  Arthroplasty candidates: {len(arthro_ranked)}")
    print()

    # Step 3: Summarize all candidates
    print("--- Step 3: Summarizing papers ---")
    subspec_ranked = summarize_papers(subspec_ranked)
    arthro_ranked = summarize_papers(arthro_ranked)
    print()

    # Step 4: Save candidates to JSON
    print("--- Step 4: Saving candidates ---")
    date_key = brief_date.strftime("%Y-%m-%d")
    output = {
        "brief_date": date_key,
        "brief_date_display": brief_date.strftime("%A, %B %d"),
        "subspecialty": subspecialty,
        "arthroplasty_slot": arthroplasty_slot,
        "subspecialty_candidates": subspec_ranked,
        "arthroplasty_candidates": arthro_ranked,
        "selected_subspecialty_index": 0,  # Default: top-ranked
        "selected_arthroplasty_index": 0,
        "status": "pending_approval",
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"{date_key}.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved to: {output_path}")
    print()

    # Step 5: Send preview email
    print("--- Step 5: Sending preview email ---")
    success = send_preview_email(
        brief_date,
        subspecialty,
        subspec_ranked,
        arthroplasty_slot,
        arthro_ranked,
    )

    if success:
        print("Evening pipeline complete. Preview sent.")
    else:
        print("WARNING: Preview email failed, but candidates are saved.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
