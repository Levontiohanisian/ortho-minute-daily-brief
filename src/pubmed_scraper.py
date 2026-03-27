"""Scrape PubMed for latest orthopaedic research papers."""

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from .config import JOURNAL_QUERY, SUBSPECIALTY_QUERIES


ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _build_query(subspecialty: str, days_back: int = 1) -> str:
    """Build PubMed search query for a subspecialty."""
    date_filter = f'("last {days_back} days"[Date - Publication])'
    journal_filter = f"({JOURNAL_QUERY})"
    subspec_filter = SUBSPECIALTY_QUERIES.get(subspecialty, "")

    if subspec_filter:
        return f"{subspec_filter} AND {journal_filter} AND {date_filter}"
    else:
        # Wildcard: search all journals, no subspecialty filter
        return f"{journal_filter} AND {date_filter}"


def _esearch(query: str, retmax: int = 50) -> list[str]:
    """Search PubMed and return list of PMIDs."""
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "sort": "date",
    })
    url = f"{ESEARCH_URL}?{params}"

    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    return data.get("esearchresult", {}).get("idlist", [])


def _efetch(pmids: list[str]) -> list[dict]:
    """Fetch paper details from PubMed for given PMIDs."""
    if not pmids:
        return []

    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    })
    url = f"{EFETCH_URL}?{params}"

    with urllib.request.urlopen(url, timeout=60) as resp:
        xml_data = resp.read().decode()

    root = ET.fromstring(xml_data)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        paper = _parse_article(article)
        if paper:
            papers.append(paper)

    return papers


def _parse_article(article: ET.Element) -> Optional[dict]:
    """Parse a single PubmedArticle XML element into a dict."""
    try:
        medline = article.find(".//MedlineCitation")
        art = medline.find(".//Article")

        # PMID
        pmid = medline.findtext("PMID", "")

        # Title
        title = art.findtext(".//ArticleTitle", "").strip()

        # Journal
        journal = art.findtext(".//Journal/Title", "")
        journal_abbrev = art.findtext(".//Journal/ISOAbbreviation", "")

        # Year
        year_el = art.find(".//Journal/JournalIssue/PubDate/Year")
        year = year_el.text if year_el is not None else ""
        if not year:
            medline_date = art.findtext(
                ".//Journal/JournalIssue/PubDate/MedlineDate", ""
            )
            year = medline_date[:4] if medline_date else ""

        # Authors
        authors = []
        for author in art.findall(".//AuthorList/Author"):
            last = author.findtext("LastName", "")
            initials = author.findtext("Initials", "")
            if last:
                authors.append(f"{last} {initials}".strip())

        # Abstract
        abstract_parts = []
        for text_el in art.findall(".//Abstract/AbstractText"):
            label = text_el.get("Label", "")
            text = "".join(text_el.itertext()).strip()
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        # Article type / study design hints
        pub_types = []
        for pt in medline.findall(".//PublicationTypeList/PublicationType"):
            pub_types.append(pt.text)

        if not title:
            return None

        return {
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "authors_short": _format_authors_short(authors),
            "journal": journal,
            "journal_abbrev": journal_abbrev,
            "year": year,
            "abstract": abstract,
            "pub_types": pub_types,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }

    except Exception as e:
        print(f"Error parsing article: {e}")
        return None


def _format_authors_short(authors: list[str]) -> str:
    """Format author list: 'Smith AB, Jones CD, et al.'"""
    if not authors:
        return "Unknown"
    if len(authors) <= 3:
        return ", ".join(authors)
    return f"{authors[0]}, {authors[1]}, et al."


def scrape_papers(subspecialty: str, days_back: int = 1) -> list[dict]:
    """
    Scrape PubMed for papers matching a subspecialty.

    Falls back to 48 hours if no results in 24 hours.
    """
    print(f"Scraping PubMed for: {subspecialty} (last {days_back} day(s))")

    query = _build_query(subspecialty, days_back=days_back)
    print(f"  Query: {query[:120]}...")

    pmids = _esearch(query)
    print(f"  Found {len(pmids)} PMIDs")

    if not pmids and days_back == 1:
        print("  No results in 24h, expanding to 48h...")
        return scrape_papers(subspecialty, days_back=2)

    if not pmids and days_back == 2:
        print("  No results in 48h, expanding to 7 days...")
        return scrape_papers(subspecialty, days_back=7)

    if not pmids:
        print("  No results found even after expanding window.")
        return []

    time.sleep(0.4)  # Respect PubMed rate limits

    papers = _efetch(pmids)
    print(f"  Fetched {len(papers)} papers")

    return papers
