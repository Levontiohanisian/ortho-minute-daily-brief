#!/usr/bin/env python3
"""
Morning pipeline: Check for approval, apply edits, send brief to Beehiiv.
Runs at 7am Pacific daily via GitHub Actions.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from src.config import PACIFIC, DATA_DIR
from src.approval_checker import check_for_approval
from src.summarizer import summarize_paper
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

    slot1_name = data["subspecialty"]
    slot2_name = data["second_slot"]
    slot1_candidates = data["subspecialty_candidates"]
    slot2_candidates = data["second_slot_candidates"]

    print(f"Slot 1: {slot1_name}")
    print(f"Slot 2: {slot2_name}")
    print(f"Slot 1 candidates: {len(slot1_candidates)}")
    print(f"Slot 2 candidates: {len(slot2_candidates)}")
    print()

    # Check for approval/edits
    print("--- Checking for editor response ---")
    approval = check_for_approval(now)

    sub_idx = data.get("selected_subspecialty_index", 0)
    sec_idx = data.get("selected_second_index", 0)

    if approval["no_response"]:
        print("No response received. Using top-ranked papers (default).")
    elif approval["approved"]:
        print("Editor approved. Using top-ranked papers.")
    else:
        if approval["swap_subspecialty"] is not None:
            new_idx = approval["swap_subspecialty"]
            if 0 <= new_idx < len(slot1_candidates):
                sub_idx = new_idx
                print(f"Swapping slot 1 paper to candidate #{new_idx + 1}")
        if approval["swap_arthroplasty"] is not None:
            new_idx = approval["swap_arthroplasty"]
            if 0 <= new_idx < len(slot2_candidates):
                sec_idx = new_idx
                print(f"Swapping slot 2 paper to candidate #{new_idx + 1}")
        if approval["edits"]:
            print(f"Edit instructions received: {approval['edits'][:200]}")

    print()

    # Select final papers
    if not slot1_candidates:
        print("ERROR: No slot 1 candidates available.")
        return 1
    if not slot2_candidates:
        print("ERROR: No slot 2 candidates available.")
        return 1

    sub_idx = min(sub_idx, len(slot1_candidates) - 1)
    sec_idx = min(sec_idx, len(slot2_candidates) - 1)

    final_slot1 = slot1_candidates[sub_idx]
    final_slot2 = slot2_candidates[sec_idx]

    print(f"Final slot 1 paper: {final_slot1['title'][:80]}...")
    print(f"Final slot 2 paper: {final_slot2['title'][:80]}...")
    print()

    # Send to Beehiiv
    print("--- Sending brief to Beehiiv ---")
    success = send_to_beehiiv(
        now,
        slot1_name,
        final_slot1,
        slot2_name,
        final_slot2,
    )

    if success:
        data["status"] = "sent"
        data["selected_subspecialty_index"] = sub_idx
        data["selected_second_index"] = sec_idx
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
