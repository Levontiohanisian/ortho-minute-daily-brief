"""Check Gmail for approval/edit replies to preview emails."""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import re

from .config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


def check_for_approval(date: datetime) -> dict:
    """
    Check Gmail for replies to the preview email.

    Returns:
        {
            "approved": bool,
            "edits": str or None,  # raw edit instructions if any
            "swap_subspecialty": int or None,  # paper number to swap to
            "swap_arthroplasty": int or None,
        }
    """
    result = {
        "approved": False,
        "edits": None,
        "swap_subspecialty": None,
        "swap_arthroplasty": None,
        "no_response": True,
    }

    date_str = date.strftime("%A, %B %d")
    search_subject = f"PREVIEW] Ortho Minute"

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select("INBOX")

        # Search for replies to preview emails from today
        since_date = (date - timedelta(days=1)).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE "{since_date}" SUBJECT "{search_subject}")'
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

            # Get body text
            body = _get_email_body(msg)
            if not body:
                continue

            body_lower = body.strip().lower()

            # Check for APPROVE
            if "approve" in body_lower:
                result["approved"] = True
                result["no_response"] = False
                break

            # Check for swap instructions
            swap_match = re.search(
                r"use #(\d+)\s+for\s+(subspecialty|arthroplasty)",
                body_lower,
            )
            if swap_match:
                num = int(swap_match.group(1))
                slot = swap_match.group(2)
                if slot == "subspecialty":
                    result["swap_subspecialty"] = num - 1  # 0-indexed
                else:
                    result["swap_arthroplasty"] = num - 1
                result["no_response"] = False

            # Check for edit instructions
            if "edit" in body_lower:
                result["edits"] = body.strip()
                result["no_response"] = False

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
