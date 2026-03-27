#!/usr/bin/env python3
"""
Evening pipeline: Scrape, score, summarize, save candidates, send preview.
Runs at 7pm Pacific daily via GitHub Actions.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from src.config import PACIFIC, DATA_DIR
from src.pubmed_scraper import scrape_papers
from src.paper_scorer import score_papers
from src.summarizer import summarize_papers
from src.preview_email import send_preview_email


def main():
    now = datetime.now(PACIFIC)
    brief_date = now + timedelta(days=1)

    print(f"=== Ortho Minute Evening Pipeline ===")
    print(f"Running at: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"Brief date: {brief_date.strftime('%A, %B %d, %Y')}")
    print()

    # Step 1: Scrape all journals
    print("--- Step 1: Scraping PubMed ---")
    papers = scrape_papers()
    print()

    if not papers:
        print("WARNING: No papers found.")
        return 1

    # Step 2: Score papers (fetch more than 10 so we have replacements)
    print("--- Step 2: Scoring papers ---")
    TARGET = 10
    POOL_SIZE = TARGET + 10  # Extra candidates in case summarization fails
    pool = score_papers(papers, top_n=POOL_SIZE)
    print(f"  Scored pool: {len(pool)} papers")
    print()

    # Step 3: Summarize top candidates, replacing failures from the pool
    print("--- Step 3: Summarizing papers ---")
    ranked = []
    pool_idx = 0
    while len(ranked) < TARGET and pool_idx < len(pool):
        # Take the next batch of unsummarized papers from the pool
        batch_end = min(pool_idx + (TARGET - len(ranked)), len(pool))
        batch = pool[pool_idx:batch_end]
        pool_idx = batch_end

        summarize_papers(batch)

        for paper in batch:
            if len(paper.get("bullets", [])) == 3:
                ranked.append(paper)
                if len(ranked) >= TARGET:
                    break
            else:
                print(f"  Dropping (no bullets): '{paper['title'][:60]}'")

    print(f"  Final candidates with bullets: {len(ranked)}")
    print()

    # Step 4: Save candidates
    print("--- Step 4: Saving candidates ---")
    date_key = brief_date.strftime("%Y-%m-%d")
    output = {
        "brief_date": date_key,
        "brief_date_display": brief_date.strftime("%A, %B %d"),
        "candidates": ranked,
        "picks": [0, 1],  # Default: top 2
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
    success = send_preview_email(brief_date, ranked)

    if success:
        print("Evening pipeline complete. Preview sent.")
    else:
        print("WARNING: Preview email failed, but candidates are saved.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
