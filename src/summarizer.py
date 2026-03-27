"""Summarize papers into 3 bullet points using Claude API."""

import json
from anthropic import Anthropic

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL


client = None


def _get_client() -> Anthropic:
    global client
    if client is None:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return client


def summarize_paper(paper: dict) -> list[str]:
    """
    Generate exactly 3 bullet points for a single paper.
    Returns list of 3 strings.
    """
    prompt = f"""You are writing for The Ortho Minute Daily Brief, a research digest for busy orthopaedic surgeons.

Summarize this paper into exactly 3 bullet points.

Rules:
- Each bullet is one line maximum
- Plain clinical English, no jargon, no statistical noise, no methods detail
- Focus on: what they found, who it applies to, what it means clinically
- No em dashes anywhere (use commas or periods instead)
- Use "orthopaedic" spelling throughout (not "orthopedic")
- No emojis
- No marketing language, no superlatives, no unnecessary adjectives
- Every bullet delivers one concrete clinical fact
- A resident between cases should understand each bullet in under 10 seconds

Paper:
Title: {paper['title']}
Journal: {paper['journal']} ({paper['year']})
Authors: {paper['authors_short']}
Abstract: {paper['abstract']}

Return ONLY a JSON array of exactly 3 strings, one per bullet point. No other text."""

    response = _get_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text.strip()

    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    bullets = json.loads(response_text)

    # Enforce no em dashes
    cleaned = []
    for b in bullets[:3]:
        b = b.replace("\u2014", ",").replace("\u2013", ",").replace("--", ",")
        b = b.replace("orthopedic", "orthopaedic")
        cleaned.append(b)

    return cleaned


def summarize_papers(papers: list[dict]) -> list[dict]:
    """Add bullet point summaries to each paper.

    Papers that fail summarization get bullets set to an empty list
    so the caller can detect and replace them.
    """
    for paper in papers:
        try:
            bullets = summarize_paper(paper)
            # Verify we got exactly 3 non-empty bullet points
            if (
                not isinstance(bullets, list)
                or len(bullets) != 3
                or any(not b or not b.strip() for b in bullets)
            ):
                raise ValueError(
                    f"Expected 3 non-empty bullets, got {bullets!r}"
                )
            paper["bullets"] = bullets
        except Exception as e:
            print(f"  FAILED summarizing '{paper['title'][:60]}': {e}")
            paper["bullets"] = []
    return papers
