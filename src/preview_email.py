"""Send preview email with candidate papers for review."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, PREVIEW_RECIPIENT, PACIFIC


def _build_preview_html(
    date: datetime,
    subspecialty: str,
    subspecialty_candidates: list[dict],
    arthroplasty_slot: str,
    arthroplasty_candidates: list[dict],
) -> str:
    """Build HTML email body for preview."""

    date_str = date.strftime("%A, %B %d")

    def paper_block(paper: dict, rank: int) -> str:
        bullets_html = ""
        for b in paper.get("bullets", []):
            bullets_html += f"    <li style='margin-bottom:4px;'>{b}</li>\n"

        score = paper.get("score", "N/A")
        reasoning = paper.get("score_reasoning", "")

        return f"""
<div style="border:1px solid #ddd; padding:16px; margin-bottom:12px; border-radius:4px;">
  <p style="color:#888; margin:0 0 4px 0; font-size:13px;">Candidate #{rank} | Score: {score}/100</p>
  <p style="color:#888; margin:0 0 8px 0; font-size:12px;">{reasoning}</p>
  <h3 style="margin:0 0 4px 0;">{paper['title']}</h3>
  <p style="color:#666; margin:0 0 8px 0;">{paper.get('journal_abbrev') or paper['journal']} ({paper['year']})</p>
  <ul style="margin:0; padding-left:20px;">
{bullets_html}  </ul>
  <p style="margin:8px 0 0 0;"><a href="{paper['link']}">PubMed Link</a></p>
</div>"""

    subspec_blocks = ""
    for i, p in enumerate(subspecialty_candidates):
        subspec_blocks += paper_block(p, i + 1)

    arthro_blocks = ""
    for i, p in enumerate(arthroplasty_candidates):
        arthro_blocks += paper_block(p, i + 1)

    html = f"""
<html>
<body style="font-family: Georgia, serif; max-width:700px; margin:0 auto; padding:20px; color:#222;">

<h1 style="font-size:22px; border-bottom:2px solid #222; padding-bottom:8px;">
  THE ORTHO MINUTE DAILY BRIEF - Preview
</h1>
<p style="color:#666;">{date_str}</p>

<p style="background:#f0f7ff; padding:12px; border-radius:4px; border:1px solid #cde;">
  <strong>Instructions:</strong> Review the candidates below. The #1 ranked paper in each section will be sent by default.<br><br>
  Reply with any of the following:<br>
  - <strong>APPROVE</strong> to send the top-ranked papers as-is<br>
  - <strong>"Use #3 for subspecialty"</strong> to swap which paper is used<br>
  - <strong>"Edit points for [paper]: [your edits]"</strong> to revise bullet points<br>
  - If no reply by midnight Pacific, top-ranked papers send automatically at 7am.
</p>

<h2 style="font-size:18px; color:#444; margin-top:24px;">
  {subspecialty} (Today's Subspecialty)
</h2>
{subspec_blocks}

<hr style="border:none; border-top:1px solid #ddd; margin:24px 0;">

<h2 style="font-size:18px; color:#444;">
  {arthroplasty_slot} (Daily Arthroplasty Slot)
</h2>
{arthro_blocks}

<hr style="border:none; border-top:1px solid #ddd; margin:24px 0;">
<p style="color:#999; font-size:12px;">This is a preview for The Ortho Minute editor. Not for distribution.</p>

</body>
</html>"""

    return html


def send_preview_email(
    date: datetime,
    subspecialty: str,
    subspecialty_candidates: list[dict],
    arthroplasty_slot: str,
    arthroplasty_candidates: list[dict],
) -> bool:
    """Send preview email to editor for review."""

    date_str = date.strftime("%A, %B %d")
    subject = f"[PREVIEW] The Ortho Minute Daily Brief | {date_str}"

    html = _build_preview_html(
        date, subspecialty, subspecialty_candidates,
        arthroplasty_slot, arthroplasty_candidates,
    )

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
