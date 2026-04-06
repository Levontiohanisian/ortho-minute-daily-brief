"""Check Gmail for approval/edit replies to preview emails."""

import imaplib
import email
import re
from datetime import datetime, timedelta

from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


def check_for_approval(date: datetime) -> dict:
    """
    Check Gmail for REPLIES to the preview email (not the original preview).

    Only matches emails with "Re:" in the subject to avoid matching the
    original sent preview email, which contains numbers in its body.

    Returns:
        {
            "picks": [int, int] or None,  # 0-indexed paper picks
            "no_response": bool,
        }
    """
    result = {
        "picks": None,
        "no_response": True,
    }

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select("INBOX")

        # Search for REPLIES only: must have "Re:" in subject
        # This excludes the original preview email we sent
        since_date = (date - timedelta(days=1)).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE "{since_date}" SUBJECT "Re:" SUBJECT "PREVIEW")'
        status, message_ids = mail.search(None, search_criteria)

        if status != "OK" or not message_ids[0]:
            print("  No reply emails found matching 'Re: ... PREVIEW'")
            mail.logout()
            return result

        ids = message_ids[0].split()
        print(f"  Found {len(ids)} reply email(s) to check.")

        for msg_id in reversed(ids):  # Most recent first
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", "")

            # Double-check: subject must start with "Re:" to be a reply
            if not subject.lower().startswith("re:"):
                print(f"  Skipping non-reply: {subject[:60]}")
                continue

            body = _get_email_body(msg)
            if not body:
                continue

            # Only look at the first few lines of the reply body
            # (ignore quoted original message which contains paper numbers)
            reply_text = _extract_reply_text(body)
            print(f"  Reply text found: '{reply_text[:100]}'")

            # Look for a number (e.g., "3" or "paper 3")
            numbers = re.findall(r'\b(\d{1,2})\b', reply_text)
            if len(numbers) >= 1:
                pick1 = int(numbers[0]) - 1  # Convert to 0-indexed
                if 0 <= pick1 <= 9:  # Sanity check: valid paper number 1-10
                    result["picks"] = [pick1]
                    result["no_response"] = False
                    print(f"  Editor picked: #{pick1 + 1}")
                    break
                else:
                    print(f"  Number {pick1 + 1} out of range, skipping.")

        mail.logout()

    except Exception as e:
        print(f"Error checking Gmail: {e}")

    return result


def _extract_reply_text(body: str) -> str:
    """Extract only the new reply text, excluding quoted original message.

    Gmail replies typically have the quoted original after a line like:
    'On Mon, Jan 1, 2024 at 5:00 AM ... wrote:'
    or after '---' or '>' quoted lines.
    """
    lines = body.strip().split("\n")
    reply_lines = []

    for line in lines:
        stripped = line.strip()
        # Stop at quoted text markers
        if stripped.startswith(">"):
            break
        if re.match(r'^On .+ wrote:$', stripped):
            break
        if stripped == "---":
            break
        if stripped.startswith("---------- Forwarded message"):
            break
        # Stop at the Gmail "On Date, Name wrote:" pattern
        if re.match(r'^On .+,.+at .+,.+wrote:', stripped):
            break
        reply_lines.append(stripped)

    return " ".join(reply_lines).strip()


def _get_email_body(msg) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""
