"""
Send the daily brief directly via Gmail SMTP to subscribers.
Subscriber list is pulled from Buttondown API automatically.
"""

import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from .config import (
    BUTTONDOWN_API_KEY,
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    WEBSITE_URL,
)


def _get_subscribers() -> list[str]:
    """Pull active subscriber emails from Buttondown API."""
    subscribers = []
    url = "https://api.buttondown.com/v1/subscribers?status=regular"

    headers = {
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
    }

    while url:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                for sub in data.get("results", []):
                    email_addr = sub.get("email_address")
                    if email_addr:
                        subscribers.append(email_addr)
                url = data.get("next")  # Pagination
        except Exception as e:
            print(f"Error fetching subscribers: {e}")
            break

    return subscribers


def _build_brief_html(date: datetime, paper: dict) -> str:
    """Build clean HTML email with no third-party branding."""

    date_str = date.strftime("%A, %B %d")
    journal_display = paper.get("journal_abbrev") or paper["journal"]

    bullets_html = ""
    for b in paper.get("bullets", []):
        bullets_html += f"<li style='margin-bottom:6px; font-size:15px; line-height:1.5;'>{b}</li>\n"

    html = f"""<html>
<body style="margin:0; padding:0; background:#ffffff;">
<table cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; margin:0 auto; font-family:Georgia, serif; color:#222; padding:32px;">

<tr><td style="border-bottom:2px solid #222; padding-bottom:12px;">
  <h1 style="font-size:20px; margin:0; letter-spacing:1px; font-weight:bold;">THE ORTHO MINUTE DAILY BRIEF</h1>
</td></tr>

<tr><td style="padding:12px 0 0 0;">
  <p style="color:#666; margin:0; font-size:14px;">{date_str}</p>
</td></tr>

<tr><td style="padding:24px 0 0 0;">
  <p style="font-size:17px; font-weight:bold; margin:0 0 6px 0; line-height:1.3;">{paper['title']}</p>
  <p style="color:#666; margin:0 0 14px 0; font-size:14px;">{journal_display} ({paper['year']})</p>
  <ul style="margin:0 0 14px 0; padding-left:20px;">
{bullets_html}  </ul>
  <p style="margin:0;"><a href="{paper['link']}" style="color:#1a5276; font-size:14px; text-decoration:underline;">Read the paper</a></p>
</td></tr>

<tr><td style="padding:24px 0 0 0;">
  <hr style="border:none; border-top:1px solid #ddd; margin:0;">
</td></tr>

<tr><td style="padding:16px 0 0 0; text-align:center;">
  <p style="color:#888; font-size:13px; margin:0 0 4px 0;"><strong>The Ortho Minute</strong></p>
  <p style="color:#888; font-size:13px; margin:0 0 4px 0;">Curated orthopaedic research. Daily.</p>
  <p style="margin:0;"><a href="{WEBSITE_URL}" style="color:#1a5276; font-size:13px;">{WEBSITE_URL}</a></p>
</td></tr>

</table>
</body>
</html>"""

    return html


def send_to_buttondown(date: datetime, paper: dict) -> bool:
    """
    Send the brief directly via Gmail SMTP to all Buttondown subscribers.
    Buttondown is only used for the subscriber list.
    """

    # Get subscriber list from Buttondown
    subscribers = _get_subscribers()
    if not subscribers:
        print("ERROR: No subscribers found. Cannot send.")
        return False

    print(f"Found {len(subscribers)} subscriber(s)")

    subject = "The Ortho Minute Daily Brief"
    html = _build_brief_html(date, paper)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)

            sent_count = 0
            for subscriber_email in subscribers:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"The Ortho Minute <{GMAIL_ADDRESS}>"
                msg["To"] = subscriber_email
                msg.attach(MIMEText(html, "html"))

                try:
                    server.sendmail(GMAIL_ADDRESS, subscriber_email, msg.as_string())
                    sent_count += 1
                except Exception as e:
                    print(f"Failed to send to {subscriber_email}: {e}")

        print(f"Brief sent to {sent_count}/{len(subscribers)} subscribers via Gmail.")
        return sent_count > 0

    except Exception as e:
        print(f"Gmail SMTP error: {e}")
        return False
