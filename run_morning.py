#!/usr/bin/env python3
"""
Morning pipeline: Check for approval, send brief to Beehiiv.
Runs at 7am Pacific daily via GitHub Actions.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from src.config import PACIFIC, DATA_DIR
from src.approval_checker import check_for_approval
from src.beehiiv_sender import send_to_beehiiv


def main():
    now = datetime.now(PACIFIC)
    date_key = now.strftime("%Y-%m-%d")

    print(f"=== Ortho Minute Morning Pipeline ===")
    print(f"Running at: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"Brief date: {date_key}")
    print()

    # Load today's candidates
    data_path = os.path.join(DATA_DIR, f"{date_key}.json")
    if not os.path.exists(data_path):
        print(f"ERROR: No candidate file found at {data_path}")
        print("The evening pipeline may not have run.")
        return 1

    with open(data_path) as f:
        data = json.load(f)

    if data.get("status") == "cancelled":
        print("Brief was cancelled. Skipping send.")
        return 0

    candidates = data["candidates"]
    picks = data.get("picks", [0, 1])

    print(f"Candidates available: {len(candidates)}")
    print()

    # Check for editor response
    print("--- Checking for editor response ---")
    approval = check_for_approval(now)

    if approval["no_response"]:
        print("No response received. Using top 2 papers (default).")
    elif approval["picks"]:
        new_picks = approval["picks"]
        # Validate picks are in range
        valid = all(0 <= p < len(candidates) for p in new_picks)
        if valid:
            picks = new_picks
            print(f"Editor picked papers #{picks[0]+1} and #{picks[1]+1}")
        else:
            print(f"Invalid picks {new_picks}, using default top 2.")

    print()

    # Select final papers
    if len(candidates) < 2:
        print("ERROR: Not enough candidates.")
        return 1

    pick1 = min(picks[0], len(candidates) - 1)
    pick2 = min(picks[1], len(candidates) - 1)

    paper1 = candidates[pick1]
    paper2 = candidates[pick2]

    print(f"Paper 1: {paper1['title'][:80]}...")
    print(f"Paper 2: {paper2['title'][:80]}...")
    print()

    # Send to Beehiiv
    print("--- Sending brief to Beehiiv ---")
    success = send_to_beehiiv(now, paper1, paper2)

    if success:
        data["status"] = "sent"
        data["picks"] = [pick1, pick2]
        with open(data_path, "w") as f:
            json.dump(data, f, indent=2)
        print("Morning pipeline complete. Brief sent to subscribers.")
    else:
        data["status"] = "send_failed"
        with open(data_path, "w") as f:
            json.dump(data, f, indent=2)
        print("ERROR: Failed to send brief to Beehiiv.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
