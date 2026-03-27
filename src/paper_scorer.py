"""Score and rank papers using Claude API."""

import json
from anthropic import Anthropic

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL


client = None


def _get_client() -> Anthropic:
    global client
    if client is None:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return client


def score_papers(papers: list[dict], top_n: int = 10) -> list[dict]:
    """
    Score and rank papers by clinical relevance. Returns top N papers
    with scores and reasoning.
    """
    if not papers:
        return []

    # Build paper summaries for Claude
    paper_list = []
    for i, p in enumerate(papers):
        entry = (
            f"Paper {i+1}:\n"
            f"Title: {p['title']}\n"
            f"Journal: {p['journal']} ({p['year']})\n"
            f"Authors: {p['authors_short']}\n"
            f"Publication Types: {', '.join(p.get('pub_types', []))}\n"
            f"Abstract: {p['abstract'][:1500]}\n"
        )
        paper_list.append(entry)

    papers_text = "\n---\n".join(paper_list)

    prompt = f"""You are an orthopaedic surgery research curator. Score and rank these papers for a daily research brief aimed at practicing orthopaedic surgeons.

Score each paper 1-100 based on:
- Clinical relevance and direct applicability to practice (40 points)
- Journal impact and prestige (20 points)
- Study design quality: RCT > prospective cohort > retrospective cohort > case series > case report (20 points)
- Sample size relative to study type (10 points)
- Novelty of findings (10 points)

Papers to score:

{papers_text}

Return a JSON array of objects, one per paper, sorted by score descending. Each object:
{{
  "paper_index": <0-based index>,
  "score": <1-100>,
  "reasoning": "<one sentence explaining the score>"
}}

Return ONLY the JSON array, no other text."""

    response = _get_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text.strip()

    # Parse JSON from response (handle markdown code blocks)
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    # Try to extract JSON array if there's extra text
    import re
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)

    # Fix trailing commas (common LLM JSON issue)
    response_text = re.sub(r',\s*([}\]])', r'\1', response_text)

    scored = json.loads(response_text)
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Attach scores to paper objects, enforcing journal diversity
    # Max 2 papers per journal so the brief spans the full journal list
    MAX_PER_JOURNAL = 2
    journal_counts = {}
    ranked_papers = []

    for entry in scored:
        if len(ranked_papers) >= top_n:
            break
        idx = entry["paper_index"]
        if 0 <= idx < len(papers):
            paper = papers[idx].copy()
            journal_key = paper.get("journal_abbrev") or paper["journal"]
            count = journal_counts.get(journal_key, 0)
            if count >= MAX_PER_JOURNAL:
                continue  # Skip, too many from this journal
            paper["score"] = entry["score"]
            paper["score_reasoning"] = entry["reasoning"]
            ranked_papers.append(paper)
            journal_counts[journal_key] = count + 1

    return ranked_papers
