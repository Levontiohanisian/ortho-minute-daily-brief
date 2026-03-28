"""Send the final brief to subscribers via Buttondown API."""

import json
import urllib.request
from datetime import datetime

from .config import (
    BUTTONDOWN_API_KEY,
    WEBSITE_URL,
)


def _build_brief_html(date: datetime, paper1: dict, paper2: dict) -> str:
    """Build the final subscriber brief HTML."""

    date_str = date.strftime("%A, %B %d")

    def paper_section(paper: dict) -> str:
        bullets = ""
        for b in paper.get("bullets", []):
            bullets += f"- {b}<br>\n"

        journal_display = paper.get("journal_abbrev") or paper["journal"]

        return f"""
<tr><td style="padding:24px 0 0 0;">
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

<tr><td style="border-bottom:2px solid #222; padding-bottom:16px;">
  <h1 style="font-size:20px; margin:0; letter-spacing:1px;">THE ORTHO MINUTE DAILY BRIEF</h1>
</td></tr>
<tr><td style="padding:12px 0 0 0;">
  <p style="color:#666; margin:0; font-size:14px;">{date_str}</p>
</td></tr>

{paper_section(paper1)}
{separator}
{paper_section(paper2)}
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


def send_to_buttondown(date: datetime, paper1: dict, paper2: dict) -> bool:
    """Send the brief to Buttondown subscribers."""

    date_str = date.strftime("%A, %B %d")
    subject = "The Ortho Minute Daily Brief"

    html = _build_brief_html(date, paper1, paper2)

    url = "https://api.buttondown.com/v1/emails"

    payload = {
        "subject": subject,
        "body": html,
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
