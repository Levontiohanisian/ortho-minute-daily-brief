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

# Weekly subspecialty rotation (0=Monday, 6=Sunday)
SUBSPECIALTY_ROTATION = {
    0: "Adult Reconstruction",
    1: "Trauma",
    2: "Foot & Ankle",
    3: "Shoulder",
    4: "Sports Medicine",
    5: "Wildcard",
    6: "Adult Reconstruction",
}

# PubMed search terms per subspecialty
SUBSPECIALTY_QUERIES = {
    "Adult Reconstruction": (
        '("total hip arthroplasty" OR "total hip replacement" OR "hip resurfacing"'
        ' OR "hip revision" OR "hip prosthesis"'
        ' OR "total knee arthroplasty" OR "total knee replacement"'
        ' OR "knee revision" OR "unicompartmental knee"'
        ' OR "total joint arthroplasty" OR "periprosthetic"'
        ' OR "joint replacement" OR "adult reconstruction")'
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

def get_today_subspecialty(date: datetime) -> str:
    return SUBSPECIALTY_ROTATION[date.weekday()]

def get_second_slot(date: datetime) -> str:
    """Second slot is Adult Reconstruction, unless today is already Adult Reconstruction,
    in which case use the next subspecialty in the rotation."""
    primary = SUBSPECIALTY_ROTATION[date.weekday()]
    if primary != "Adult Reconstruction":
        return "Adult Reconstruction"
    # On Adult Reconstruction days, use the next day's subspecialty as second slot
    next_day = (date.weekday() + 1) % 7
    return SUBSPECIALTY_ROTATION[next_day]

# Claude model for scoring/summarization
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "daily")
