"""Send the final brief to subscribers via Buttondown API."""

import json
import urllib.request
from datetime import datetime

from .config import (
    BUTTONDOWN_API_KEY,
    WEBSITE_URL,
)


def _build_brief_markdown(date: datetime, paper1: dict, paper2: dict) -> str:
    """Build the final subscriber brief in markdown (Buttondown's native format)."""

    date_str = date.strftime("%A, %B %d")

    def paper_section(paper: dict) -> str:
        journal_display = paper.get("journal_abbrev") or paper["journal"]
        bullets = ""
        for b in paper.get("bullets", []):
            bullets += f"- {b}\n"

        return (
            f"**{paper['title']}**\n\n"
            f"*{journal_display} ({paper['year']})*\n\n"
            f"{bullets}\n"
            f"[Read the paper]({paper['link']})"
        )

    brief = (
        f"# THE ORTHO MINUTE DAILY BRIEF\n\n"
        f"---\n\n"
        f"{date_str}\n\n"
        f"{paper_section(paper1)}\n\n"
        f"---\n\n"
        f"{paper_section(paper2)}\n\n"
        f"---\n\n"
        f"**The Ortho Minute**\n\n"
        f"Curated orthopaedic research. Daily.\n\n"
        f"[theorthominute.com]({WEBSITE_URL})"
    )

    return brief


def send_to_buttondown(date: datetime, paper1: dict, paper2: dict) -> bool:
    """Send the brief to Buttondown subscribers."""

    subject = "The Ortho Minute Daily Brief"

    body = _build_brief_markdown(date, paper1, paper2)

    url = "https://api.buttondown.com/v1/emails"

    payload = {
        "subject": subject,
        "body": body,
        "status": "about_to_send",
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        "X-Buttondown-Live-Dangerously": "true",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode())
            email_id = response_data.get("id", "unknown")
            print(f"Brief sent to Buttondown. Email ID: {email_id}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Buttondown API error ({e.code}): {error_body}")

        print("Retrying Buttondown send...")
        try:
            req2 = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req2, timeout=30) as resp:
                print("Retry successful.")
                return True
        except Exception as retry_err:
            print(f"Retry also failed: {retry_err}")
            return False
    except Exception as e:
        print(f"Failed to send to Buttondown: {e}")
        return False
