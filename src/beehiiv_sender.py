"""Send the final brief to subscribers via Beehiiv API."""

import json
import urllib.request
from datetime import datetime

from .config import (
    BEEHIIV_API_KEY,
    BEEHIIV_PUBLICATION_ID,
    WEBSITE_URL,
)


def _build_brief_html(
    date: datetime,
    subspecialty: str,
    subspecialty_paper: dict,
    arthroplasty_slot: str,
    arthroplasty_paper: dict,
) -> str:
    """Build the final subscriber brief HTML."""

    date_str = date.strftime("%A, %B %d")

    def paper_section(section_title: str, paper: dict) -> str:
        bullets = ""
        for b in paper.get("bullets", []):
            bullets += f"- {b}<br>\n"

        journal_display = paper.get("journal_abbrev") or paper["journal"]

        return f"""
<tr><td style="padding:24px 0 0 0;">
  <p style="font-size:11px; letter-spacing:2px; color:#888; margin:0 0 12px 0;">{section_title.upper()}</p>
  <p style="font-size:17px; font-weight:bold; margin:0 0 4px 0; line-height:1.3;">{paper['title']}</p>
  <p style="color:#666; margin:0 0 12px 0; font-size:14px;">{journal_display} ({paper['year']})</p>
  <p style="font-size:15px; line-height:1.6; margin:0 0 12px 0;">
{bullets}  </p>
  <p style="margin:0;"><a href="{paper['link']}" style="color:#1a5276; font-size:14px;">Read the paper</a></p>
</td></tr>"""

    separator = """
<tr><td style="padding:16px 0;">
  <hr style="border:none; border-top:1px solid #ddd; margin:0;">
</td></tr>"""

    html = f"""
<html>
<body style="margin:0; padding:0; background:#f9f9f9;">
<table cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; margin:0 auto; font-family:Georgia, serif; color:#222; background:#fff; padding:32px;">

<tr><td style="padding-bottom:16px; border-bottom:2px solid #222;">
  <h1 style="font-size:20px; margin:0; letter-spacing:1px;">THE ORTHO MINUTE DAILY BRIEF</h1>
  <p style="color:#666; margin:4px 0 0 0; font-size:14px;">{date_str}</p>
</td></tr>

{paper_section(subspecialty, subspecialty_paper)}
{separator}
{paper_section(arthroplasty_slot, arthroplasty_paper)}
{separator}

<tr><td style="padding:24px 0 0 0; text-align:center;">
  <p style="color:#888; font-size:13px; margin:0 0 4px 0;"><strong>The Ortho Minute</strong></p>
  <p style="color:#888; font-size:13px; margin:0 0 4px 0;">Curated orthopaedic research. Daily.</p>
  <p style="margin:0;"><a href="{WEBSITE_URL}" style="color:#1a5276; font-size:13px;">{WEBSITE_URL}</a></p>
</td></tr>

</table>
</body>
</html>"""

    return html


def _build_brief_text(
    date: datetime,
    subspecialty: str,
    subspecialty_paper: dict,
    arthroplasty_slot: str,
    arthroplasty_paper: dict,
) -> str:
    """Build plain text version of the brief."""

    date_str = date.strftime("%A, %B %d")

    def paper_block(title: str, paper: dict) -> str:
        journal_display = paper.get("journal_abbrev") or paper["journal"]
        bullets = "\n".join(f"- {b}" for b in paper.get("bullets", []))
        return f"""{title.upper()}

{paper['title']}
{journal_display} ({paper['year']})

{bullets}

Read the paper: {paper['link']}"""

    return f"""THE ORTHO MINUTE DAILY BRIEF
{date_str}

-----

{paper_block(subspecialty, subspecialty_paper)}

-----

{paper_block(arthroplasty_slot, arthroplasty_paper)}

-----

The Ortho Minute
Curated orthopaedic research. Daily.
{WEBSITE_URL}"""


def send_to_beehiiv(
    date: datetime,
    subspecialty: str,
    subspecialty_paper: dict,
    arthroplasty_slot: str,
    arthroplasty_paper: dict,
) -> bool:
    """Send the brief to Beehiiv subscribers."""

    date_str = date.strftime("%A, %B %d")
    subject = f"Ortho Minute Daily Brief | {subspecialty} + {arthroplasty_slot} | {date_str}"

    html = _build_brief_html(
        date, subspecialty, subspecialty_paper,
        arthroplasty_slot, arthroplasty_paper,
    )

    # Beehiiv API: Create a post and schedule/publish it
    url = f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUBLICATION_ID}/posts"

    payload = {
        "title": subject,
        "subtitle": f"{subspecialty} + {arthroplasty_slot}",
        "status": "confirmed",  # Sends immediately
        "content_html": html,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEEHIIV_API_KEY}",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode())
            post_id = response_data.get("data", {}).get("id", "unknown")
            print(f"Brief sent to Beehiiv. Post ID: {post_id}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Beehiiv API error ({e.code}): {error_body}")

        # Retry once
        print("Retrying Beehiiv send...")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print("Retry successful.")
                return True
        except Exception as retry_err:
            print(f"Retry also failed: {retry_err}")
            return False
    except Exception as e:
        print(f"Failed to send to Beehiiv: {e}")
        return False
