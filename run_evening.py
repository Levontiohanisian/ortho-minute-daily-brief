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
    get_second_slot,
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

    slot1 = get_today_subspecialty(brief_date)
    slot2 = get_second_slot(brief_date)

    print(f"Slot 1: {slot1}")
    print(f"Slot 2: {slot2}")
    print()

    # Step 1: Scrape papers for both slots
    print("--- Step 1: Scraping PubMed ---")
    slot1_papers = scrape_papers(slot1)
    slot2_papers = scrape_papers(slot2)
    print()

    if not slot1_papers:
        print(f"WARNING: No papers found for {slot1}")
    if not slot2_papers:
        print(f"WARNING: No papers found for {slot2}")

    # Step 2: Score papers
    print("--- Step 2: Scoring papers ---")
    slot1_ranked = score_papers(slot1_papers, slot1, top_n=5)
    slot2_ranked = score_papers(slot2_papers, slot2, top_n=5)
    print(f"  Slot 1 candidates: {len(slot1_ranked)}")
    print(f"  Slot 2 candidates: {len(slot2_ranked)}")
    print()

    # Step 3: Summarize all candidates
    print("--- Step 3: Summarizing papers ---")
    slot1_ranked = summarize_papers(slot1_ranked)
    slot2_ranked = summarize_papers(slot2_ranked)
    print()

    # Step 4: Save candidates to JSON
    print("--- Step 4: Saving candidates ---")
    date_key = brief_date.strftime("%Y-%m-%d")
    output = {
        "brief_date": date_key,
        "brief_date_display": brief_date.strftime("%A, %B %d"),
        "subspecialty": slot1,
        "second_slot": slot2,
        "subspecialty_candidates": slot1_ranked,
        "second_slot_candidates": slot2_ranked,
        "selected_subspecialty_index": 0,
        "selected_second_index": 0,
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
        slot1,
        slot1_ranked,
        slot2,
        slot2_ranked,
    )

    if success:
        print("Evening pipeline complete. Preview sent.")
    else:
        print("WARNING: Preview email failed, but candidates are saved.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
