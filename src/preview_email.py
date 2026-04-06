"""Send preview email with candidate papers for review."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, PREVIEW_RECIPIENT


def _build_preview_html(date: datetime, candidates: list[dict]) -> str:
    """Build HTML email body for preview."""

    date_str = date.strftime("%A, %B %d")

    paper_blocks = ""
    for i, paper in enumerate(candidates):
        bullets_html = ""
        for b in paper.get("bullets", []):
            bullets_html += f"    <li style='margin-bottom:4px;'>{b}</li>\n"

        score = paper.get("score", "N/A")
        reasoning = paper.get("score_reasoning", "")
        journal_display = paper.get("journal_abbrev") or paper["journal"]

        paper_blocks += f"""
<div style="border:1px solid #ddd; padding:16px; margin-bottom:12px; border-radius:4px;">
  <p style="font-size:18px; font-weight:bold; margin:0 0 4px 0;">#{i+1}</p>
  <p style="color:#888; margin:0 0 8px 0; font-size:12px;">Score: {score}/100 | {reasoning}</p>
  <h3 style="margin:0 0 4px 0;">{paper['title']}</h3>
  <p style="color:#666; margin:0 0 8px 0;">{journal_display} ({paper['year']})</p>
  <ul style="margin:0; padding-left:20px;">
{bullets_html}  </ul>
  <p style="margin:8px 0 0 0;"><a href="{paper['link']}">PubMed Link</a></p>
</div>"""

    html = f"""
<html>
<body style="font-family: Georgia, serif; max-width:700px; margin:0 auto; padding:20px; color:#222;">

<h1 style="font-size:22px; border-bottom:2px solid #222; padding-bottom:8px;">
  THE ORTHO MINUTE DAILY BRIEF - Preview
</h1>
<p style="color:#666;">{date_str}</p>

<p style="background:#f0f7ff; padding:12px; border-radius:4px; border:1px solid #cde;">
  <strong>Reply with one number to pick your paper.</strong><br><br>
  Example: <strong>3</strong><br><br>
  If no reply within 2 hours, paper #1 sends automatically.
</p>

{paper_blocks}

<hr style="border:none; border-top:1px solid #ddd; margin:24px 0;">
<p style="color:#999; font-size:12px;">This is a preview for The Ortho Minute editor. Not for distribution.</p>

</body>
</html>"""

    return html


def send_preview_email(date: datetime, candidates: list[dict]) -> bool:
    """Send preview email to editor for review.

    Papers without exactly 3 bullet points are filtered out as a safety net.
    """
    # Safety net: never include a paper missing bullet points
    candidates = [
        p for p in candidates
        if isinstance(p.get("bullets"), list) and len(p["bullets"]) == 3
    ]

    if not candidates:
        print("ERROR: No candidates with valid bullet points. Cannot send preview.")
        return False

    date_str = date.strftime("%A, %B %d")
    subject = f"[PREVIEW] The Ortho Minute Daily Brief | {date_str}"

    html = _build_preview_html(date, candidates)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = PREVIEW_RECIPIENT
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, PREVIEW_RECIPIENT, msg.as_string())
        print(f"Preview email sent to {PREVIEW_RECIPIENT}")
        return True
    except Exception as e:
        print(f"Failed to send preview email: {e}")
        return False
