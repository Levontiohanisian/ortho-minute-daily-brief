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

            # Only look at the FIRST non-empty line of the reply.
            # The editor's reply is just a number (e.g., "8").
            # We ignore everything else to avoid picking up numbers
            # from the quoted original preview email.
            first_line = _get_first_line(body)
            print(f"  First line of reply: '{first_line}'")

            # The first line should be just a number 1-10
            match = re.match(r'^\s*(\d{1,2})\s*$', first_line)
            if match:
                pick1 = int(match.group(1)) - 1  # Convert to 0-indexed
                if 0 <= pick1 <= 9:  # Valid paper number 1-10
                    result["picks"] = [pick1]
                    result["no_response"] = False
                    print(f"  Editor picked: #{pick1 + 1}")
                    break
                else:
                    print(f"  Number {pick1 + 1} out of range (must be 1-10).")
            else:
                # Also try: first line contains a number among short text
                # e.g., "send 8" or "paper 8" or "#8"
                short_match = re.search(r'#?(\d{1,2})\b', first_line)
                if short_match and len(first_line) < 30:
                    pick1 = int(short_match.group(1)) - 1
                    if 0 <= pick1 <= 9:
                        result["picks"] = [pick1]
                        result["no_response"] = False
                        print(f"  Editor picked: #{pick1 + 1}")
                        break
                print(f"  Could not parse a paper number from first line.")

        mail.logout()

    except Exception as e:
        print(f"Error checking Gmail: {e}")

    return result


def _get_first_line(body: str) -> str:
    """Get the first non-empty line of an email body.

    For reply parsing, we only care about the first line because the
    editor's reply is just a number. Everything after that is either
    blank lines, signatures, or quoted original message content that
    contains paper numbers and would cause false matches.
    """
    for line in body.strip().split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


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
