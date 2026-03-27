"""Configuration constants for The Ortho Minute Daily Brief."""

import os
from datetime import datetime, timezone, timedelta

# Timezone
PACIFIC = timezone(timedelta(hours=-7))  # PDT; change to -8 for PST

# API Keys (loaded from environment / GitHub Secrets)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY", "")
BEEHIIV_PUBLICATION_ID = os.environ.get("BEEHIIV_PUBLICATION_ID", "")
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
}

# Journal name for PubMed query
JOURNAL_QUERY = " OR ".join(
    f'"{name}"[Journal]' for name in JOURNALS.values()
)

# Weekly subspecialty rotation (0=Monday, 6=Sunday)
SUBSPECIALTY_ROTATION = {
    0: "Total Hip Arthroplasty",
    1: "Total Knee Arthroplasty",
    2: "Trauma",
    3: "Foot & Ankle",
    4: "Shoulder",
    5: "Sports Medicine",
    6: "Wildcard",
}

# PubMed search terms per subspecialty
SUBSPECIALTY_QUERIES = {
    "Total Hip Arthroplasty": (
        '("total hip arthroplasty" OR "total hip replacement" OR "hip resurfacing"'
        ' OR "hip revision" OR "hip prosthesis")'
    ),
    "Total Knee Arthroplasty": (
        '("total knee arthroplasty" OR "total knee replacement"'
        ' OR "knee revision" OR "unicompartmental knee")'
    ),
    "Trauma": (
        '("fracture fixation" OR "fracture management" OR "orthopaedic trauma"'
        ' OR "nonunion" OR "malunion" OR "open fracture" OR "pelvic fracture"'
        ' OR "polytrauma")'
    ),
    "Foot & Ankle": (
        '("foot" OR "ankle" OR "hallux" OR "metatarsal" OR "calcaneus"'
        ' OR "Achilles" OR "ankle arthroplasty" OR "ankle arthrodesis")'
    ),
    "Shoulder": (
        '("shoulder arthroplasty" OR "rotator cuff" OR "shoulder replacement"'
        ' OR "reverse shoulder" OR "shoulder instability" OR "labral"'
        ' OR "proximal humerus")'
    ),
    "Sports Medicine": (
        '("ACL" OR "anterior cruciate" OR "meniscus" OR "ligament reconstruction"'
        ' OR "sports medicine" OR "cartilage repair" OR "arthroscopy"'
        ' OR "tendon repair")'
    ),
    "Wildcard": "",  # No subspecialty filter for wildcard
}

# Arthroplasty alternation: even days = THA, odd days = TKA
def get_arthroplasty_slot(date: datetime) -> str:
    return "Total Hip Arthroplasty" if date.day % 2 == 0 else "Total Knee Arthroplasty"

def get_today_subspecialty(date: datetime) -> str:
    return SUBSPECIALTY_ROTATION[date.weekday()]

# Claude model for scoring/summarization
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "daily")
