#!/usr/bin/env python3
"""
Combined morning pipeline:
1. Check if today's preview was already sent (prevent duplicate runs)
2. Scrape PubMed, score, summarize, send preview
3. Poll inbox every 2 minutes for editor reply (up to 2 hours)
4. Send to subscribers immediately when reply is found
5. If no reply after 2 hours, auto-send paper #1
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from src.config import PACIFIC, DATA_DIR
from src.pubmed_scraper import scrape_papers
from src.paper_scorer import score_papers
from src.summarizer import summarize_papers
from src.preview_email import send_preview_email
from src.approval_checker import check_for_approval
from src.buttondown_sender import send_to_buttondown


def load_existing_data():
    """Check if today's data file already exists. Returns (data, path) or (None, path)."""
    now = datetime.now(PACIFIC)
    date_key = now.strftime("%Y-%m-%d")
    data_path = os.path.join(DATA_DIR, f"{date_key}.json")

    if os.path.exists(data_path):
        with open(data_path) as f:
            return json.load(f), data_path
    return None, data_path


def scrape_and_preview():
    """Scrape papers, score, summarize, send preview. Returns candidates list."""
    now = datetime.now(PACIFIC)

    print(f"=== Ortho Minute Morning Pipeline ===")
    print(f"Running at: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print()

    # Step 1: Scrape
    print("--- Step 1: Scraping PubMed ---")
    papers = scrape_papers()
    print()
    if not papers:
        print("WARNING: No papers found.")
        return None, None, None

    # Step 2: Score
    print("--- Step 2: Scoring papers ---")
    TARGET = 10
    POOL_SIZE = TARGET + 10
    pool = score_papers(papers, top_n=POOL_SIZE)
    print(f"  Scored pool: {len(pool)} papers")
    print()

    # Step 3: Summarize
    print("--- Step 3: Summarizing papers ---")
    ranked = []
    pool_idx = 0
    while len(ranked) < TARGET and pool_idx < len(pool):
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

    # Step 4: Save
    date_key = now.strftime("%Y-%m-%d")
    preview_sent_at = datetime.now(PACIFIC)
    output = {
        "brief_date": date_key,
        "brief_date_display": now.strftime("%A, %B %d"),
        "candidates": ranked,
        "picks": [0],
        "status": "pending_approval",
        "preview_sent_at": preview_sent_at.isoformat(),
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"{date_key}.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved to: {output_path}")

    # Step 5: Send preview
    print("--- Step 5: Sending preview email ---")
    send_preview_email(now, ranked)

    return ranked, output_path, preview_sent_at


def wait_for_reply_and_send(candidates, data_path, preview_sent_at, max_wait_minutes=120):
    """Poll inbox every 2 minutes. Send as soon as reply is found.
    After max_wait_minutes, auto-send paper #1."""

    print()
    print(f"--- Waiting for editor reply (up to {max_wait_minutes} min) ---")
    print(f"  Only considering replies after: {preview_sent_at.isoformat()}")

    start = time.time()
    poll_interval = 120  # 2 minutes

    while True:
        elapsed = (time.time() - start) / 60
        if elapsed >= max_wait_minutes:
            print(f"No reply after {max_wait_minutes} minutes. Auto-sending paper #1.")
            paper = candidates[0]
            now = datetime.now(PACIFIC)
            success = send_to_buttondown(now, paper)
            if success:
                with open(data_path) as f:
                    data = json.load(f)
                data["status"] = "sent"
                data["picks"] = [0]
                with open(data_path, "w") as f:
                    json.dump(data, f, indent=2)
                print("AUTO-SENT paper #1 successfully.")
            else:
                print("ERROR: Auto-send failed.")
            return

        now = datetime.now(PACIFIC)
        approval = check_for_approval(now, preview_sent_at=preview_sent_at)

        if not approval["no_response"]:
            pick = approval["picks"][0]
            pick = min(pick, len(candidates) - 1)
            paper = candidates[pick]

            print(f"Editor picked paper #{pick + 1}: {paper['title'][:60]}...")
            print()
            print("--- Sending to subscribers NOW ---")

            success = send_to_buttondown(now, paper)
            if success:
                with open(data_path) as f:
                    data = json.load(f)
                data["status"] = "sent"
                data["picks"] = [pick]
                with open(data_path, "w") as f:
                    json.dump(data, f, indent=2)
                print("SENT SUCCESSFULLY.")
            else:
                print("ERROR: Send failed.")
            return

        remaining = max_wait_minutes - elapsed
        print(f"  No reply yet. Checking again in 2 min ({remaining:.0f} min remaining)...")
        time.sleep(poll_interval)


def main():
    # Check if today's pipeline already ran
    existing, data_path = load_existing_data()

    if existing:
        status = existing.get("status", "")

        if status == "sent":
            print(f"Today's brief already sent. Nothing to do.")
            return 0

        if status == "pending_approval" and existing.get("preview_sent_at"):
            # Preview already sent today -- don't send another one.
            # Just resume waiting for the reply.
            print(f"Preview already sent today. Resuming reply wait.")
            candidates = existing["candidates"]
            preview_sent_at = datetime.fromisoformat(existing["preview_sent_at"])
            wait_for_reply_and_send(candidates, data_path, preview_sent_at, max_wait_minutes=120)
            return 0

    # Fresh run: scrape, preview, wait
    candidates, data_path, preview_sent_at = scrape_and_preview()
    if not candidates:
        return 1

    wait_for_reply_and_send(candidates, data_path, preview_sent_at, max_wait_minutes=120)
    return 0


if __name__ == "__main__":
    sys.exit(main())
