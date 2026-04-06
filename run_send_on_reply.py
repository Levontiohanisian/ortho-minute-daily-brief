#!/usr/bin/env python3
"""
Send-on-reply: Checks for editor reply and sends immediately.
Runs every 10 minutes after the morning preview.
If no reply by 5 hours after preview, sends #1 automatically.
"""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from src.config import PACIFIC, DATA_DIR
from src.approval_checker import check_for_approval
from src.buttondown_sender import send_to_buttondown


def main():
    now = datetime.now(PACIFIC)
    date_key = now.strftime("%Y-%m-%d")

    print(f"=== Send-On-Reply Check ===")
    print(f"Running at: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"Date: {date_key}")
    print()

    # Load today's candidates
    data_path = os.path.join(DATA_DIR, f"{date_key}.json")
    if not os.path.exists(data_path):
        print("No candidate file for today. Skipping.")
        return 0

    with open(data_path) as f:
        data = json.load(f)

    # Already sent or cancelled? Skip.
    status = data.get("status", "")
    if status in ("sent", "cancelled"):
        print(f"Brief already {status}. Nothing to do.")
        return 0

    if status != "pending_approval":
        print(f"Unexpected status: {status}. Skipping.")
        return 0

    candidates = data["candidates"]
    print(f"Candidates available: {len(candidates)}")

    # Filter out candidates missing bullet points
    valid_candidates = [
        p for p in candidates
        if isinstance(p.get("bullets"), list) and len(p["bullets"]) == 3
    ]
    if len(valid_candidates) < len(candidates):
        dropped = len(candidates) - len(valid_candidates)
        print(f"Dropped {dropped} candidate(s) missing bullet points.")
        candidates = valid_candidates

    if not candidates:
        print("ERROR: No valid candidates.")
        return 1

    # Check for editor reply
    print("Checking for editor reply...")
    approval = check_for_approval(now)

    if approval["no_response"]:
        # Check if 5 hours have passed since preview (auto-send #1)
        preview_time = data.get("preview_sent_at")
        if preview_time:
            from datetime import timezone
            preview_dt = datetime.fromisoformat(preview_time)
            hours_since = (now - preview_dt).total_seconds() / 3600
            if hours_since >= 2:
                print(f"No reply after {hours_since:.1f} hours. Auto-sending #1.")
                pick = 0
            else:
                print(f"No reply yet ({hours_since:.1f} hours since preview). Waiting.")
                return 0
        else:
            print("No reply and no preview timestamp. Waiting.")
            return 0
    else:
        pick = approval["picks"][0]
        print(f"Editor picked paper #{pick + 1}")

    # Send
    pick = min(pick, len(candidates) - 1)
    paper = candidates[pick]
    print(f"Sending: {paper['title'][:80]}...")
    print()

    success = send_to_buttondown(now, paper)

    if success:
        data["status"] = "sent"
        data["picks"] = [pick]
        with open(data_path, "w") as f:
            json.dump(data, f, indent=2)
        print("Brief sent to subscribers.")
    else:
        print("ERROR: Failed to send.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
