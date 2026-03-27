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

    subspecialty = data["subspecialty"]
    arthroplasty_slot = data["arthroplasty_slot"]
    subspec_candidates = data["subspecialty_candidates"]
    arthro_candidates = data["arthroplasty_candidates"]

    print(f"Subspecialty: {subspecialty}")
    print(f"Arthroplasty: {arthroplasty_slot}")
    print(f"Subspecialty candidates: {len(subspec_candidates)}")
    print(f"Arthroplasty candidates: {len(arthro_candidates)}")
    print()

    # Check for approval/edits
    print("--- Checking for editor response ---")
    approval = check_for_approval(now)

    sub_idx = data.get("selected_subspecialty_index", 0)
    art_idx = data.get("selected_arthroplasty_index", 0)

    if approval["no_response"]:
        print("No response received. Using top-ranked papers (default).")
    elif approval["approved"]:
        print("Editor approved. Using top-ranked papers.")
    else:
        if approval["swap_subspecialty"] is not None:
            new_idx = approval["swap_subspecialty"]
            if 0 <= new_idx < len(subspec_candidates):
                sub_idx = new_idx
                print(f"Swapping subspecialty paper to candidate #{new_idx + 1}")
        if approval["swap_arthroplasty"] is not None:
            new_idx = approval["swap_arthroplasty"]
            if 0 <= new_idx < len(arthro_candidates):
                art_idx = new_idx
                print(f"Swapping arthroplasty paper to candidate #{new_idx + 1}")
        if approval["edits"]:
            print(f"Edit instructions received: {approval['edits'][:200]}")
            # Re-summarize affected papers with edit context
            # For now, keep existing summaries (edits would need more complex parsing)

    print()

    # Select final papers
    if not subspec_candidates:
        print("ERROR: No subspecialty candidates available.")
        return 1
    if not arthro_candidates:
        print("ERROR: No arthroplasty candidates available.")
        return 1

    sub_idx = min(sub_idx, len(subspec_candidates) - 1)
    art_idx = min(art_idx, len(arthro_candidates) - 1)

    final_subspec = subspec_candidates[sub_idx]
    final_arthro = arthro_candidates[art_idx]

    print(f"Final subspecialty paper: {final_subspec['title'][:80]}...")
    print(f"Final arthroplasty paper: {final_arthro['title'][:80]}...")
    print()

    # Send to Beehiiv
    print("--- Sending brief to Beehiiv ---")
    success = send_to_beehiiv(
        now,
        subspecialty,
        final_subspec,
        arthroplasty_slot,
        final_arthro,
    )

    if success:
        # Update status
        data["status"] = "sent"
        data["selected_subspecialty_index"] = sub_idx
        data["selected_arthroplasty_index"] = art_idx
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
