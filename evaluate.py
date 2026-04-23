from __future__ import annotations

import math
import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"\b\w+\b")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if len(tokens) < n or n <= 0:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def rouge_n(candidate: str, reference: str, n: int) -> float:
    candidate_ngrams = Counter(ngrams(tokenize(candidate), n))
    reference_ngrams = Counter(ngrams(tokenize(reference), n))
    if not candidate_ngrams or not reference_ngrams:
        return 0.0

    overlap = sum((candidate_ngrams & reference_ngrams).values())
    candidate_total = sum(candidate_ngrams.values())
    reference_total = sum(reference_ngrams.values())

    precision = overlap / candidate_total if candidate_total else 0.0
    recall = overlap / reference_total if reference_total else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0

    previous = [0] * (len(b) + 1)
    current = [0] * (len(b) + 1)

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                current[j] = previous[j - 1] + 1
            else:
                current[j] = max(previous[j], current[j - 1])
        previous, current = current, [0] * (len(b) + 1)
    return previous[-1]


def rouge_l(candidate: str, reference: str) -> float:
    candidate_tokens = tokenize(candidate)
    reference_tokens = tokenize(reference)
    if not candidate_tokens or not reference_tokens:
        return 0.0

    lcs = lcs_length(candidate_tokens, reference_tokens)
    precision = lcs / len(candidate_tokens)
    recall = lcs / len(reference_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_rouge_scores(candidate: str, reference: str) -> dict[str, float]:
    return {
        "rouge1": round(rouge_n(candidate, reference, 1), 4),
        "rouge2": round(rouge_n(candidate, reference, 2), 4),
        "rougeL": round(rouge_l(candidate, reference), 4),
    }


def average_scores(score_rows: list[dict[str, float]]) -> dict[str, float]:
    if not score_rows:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    keys = ("rouge1", "rouge2", "rougeL")
    averages = {}
    for key in keys:
        averages[key] = round(sum(row[key] for row in score_rows) / len(score_rows), 4)
    return averages


def safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def safe_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = safe_mean(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)
