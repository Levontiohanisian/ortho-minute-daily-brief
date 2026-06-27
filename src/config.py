"""Configuration constants for The Ortho Minute Daily Brief."""

import os
from datetime import datetime, timezone, timedelta

# Timezone
PACIFIC = timezone(timedelta(hours=-7))  # PDT; change to -8 for PST

# API Keys (loaded from environment / GitHub Secrets)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY", "")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "info@theorthominute.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
PREVIEW_RECIPIENT = os.environ.get("PREVIEW_RECIPIENT", "info@theorthominute.com")

# Website
WEBSITE_URL = "https://theorthominute.com"

# PubMed journals to search
JOURNALS = {
    "JBJS": "J Bone Joint Surg Am",
    "CORR": "Clin Orthop Relat Res",
    "Arthroplasty Today": "Arthroplasty Today",
    "J Arthroplasty": "J Arthroplasty",
    "Foot Ankle Int": "Foot Ankle Int",
    "AJSM": "Am J Sports Med",
    "KSSTA": "Knee Surg Sports Traumatol Arthrosc",
    "J Orthop Trauma": "J Orthop Trauma",
    "J Hand Surg Am": "J Hand Surg Am",
    "JAAOS": "J Am Acad Orthop Surg",
    "J Pediatr Orthop": "J Pediatr Orthop",
    "J Shoulder Elbow Surg": "J Shoulder Elbow Surg",
}

# Journal name for PubMed query
JOURNAL_QUERY = " OR ".join(
    f'"{name}"[Journal]' for name in JOURNALS.values()
)

# Claude model for scoring/summarization
CLAUDE_MODEL = "claude-sonnet-4-6"

# Data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "daily")
