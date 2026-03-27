"""Check Gmail for approval/edit replies to preview emails."""

import imaplib
import email
import re
from datetime import datetime, timedelta

from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


def check_for_approval(date: datetime) -> dict:
    """
    Check Gmail for replies to the preview email.

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

        # Search for replies to preview emails from today
        since_date = (date - timedelta(days=1)).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE "{since_date}" SUBJECT "PREVIEW")'
        status, message_ids = mail.search(None, search_criteria)

        if status != "OK" or not message_ids[0]:
            mail.logout()
            return result

        ids = message_ids[0].split()

        for msg_id in reversed(ids):  # Most recent first
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            body = _get_email_body(msg)
            if not body:
                continue

            body = body.strip()

            # Look for two numbers (e.g., "1, 4" or "1 4" or "1 and 4")
            numbers = re.findall(r'\b(\d{1,2})\b', body)
            if len(numbers) >= 2:
                pick1 = int(numbers[0]) - 1  # Convert to 0-indexed
                pick2 = int(numbers[1]) - 1
                result["picks"] = [pick1, pick2]
                result["no_response"] = False
                break

        mail.logout()

    except Exception as e:
        print(f"Error checking Gmail: {e}")

    return result


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
