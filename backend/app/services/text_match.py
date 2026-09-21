import re


def tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


def score_overlap(query_tokens: set[str], candidate_text: str) -> float:
    if not query_tokens:
        return 0.0
    candidate_tokens = tokenize(candidate_text)
    if not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens)
    return min(1.0, overlap / len(query_tokens))
