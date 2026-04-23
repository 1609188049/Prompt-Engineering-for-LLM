from __future__ import annotations

import math
import os
import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"\b\w+\b")
NUMERIC_FACT_PATTERN = re.compile(r"\b\d[\d,./:-]*%?\b")
ENTITY_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|[A-Z]{2,}(?:\s+[A-Z]{2,})*)\b")
DEFAULT_BERTSCORE_MODEL = os.getenv("BERTSCORE_MODEL", "distilbert-base-uncased")
DEFAULT_BERTSCORE_LANG = os.getenv("BERTSCORE_LANG", "en")
METRIC_KEYS = (
    "bertscore_precision",
    "bertscore_recall",
    "bertscore_f1",
    "novel_1gram_ratio",
    "novel_2gram_ratio",
    "compression_ratio",
    "grounding_score",
    "non_redundancy_score",
    "length_score",
    "rule_based_quality",
)

_BERT_SCORER = None
_BERT_SCORER_SETTINGS: tuple[str, str] | None = None


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if len(tokens) < n or n <= 0:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def get_bert_scorer():
    global _BERT_SCORER, _BERT_SCORER_SETTINGS

    settings = (DEFAULT_BERTSCORE_MODEL, DEFAULT_BERTSCORE_LANG)
    if _BERT_SCORER is not None and _BERT_SCORER_SETTINGS == settings:
        return _BERT_SCORER

    try:
        from bert_score import BERTScorer
    except ImportError as exc:
        raise RuntimeError(
            "bert-score is not installed. Run `pip install -r requirements.txt` before evaluation."
        ) from exc

    _BERT_SCORER = BERTScorer(
        model_type=DEFAULT_BERTSCORE_MODEL,
        lang=DEFAULT_BERTSCORE_LANG,
        rescale_with_baseline=False,
    )
    _BERT_SCORER_SETTINGS = settings
    return _BERT_SCORER


def compute_bert_scores(candidate: str, reference: str) -> dict[str, float]:
    scorer = get_bert_scorer()
    precision, recall, f1 = scorer.score([candidate], [reference])
    return {
        "bertscore_precision": round(float(precision[0]), 4),
        "bertscore_recall": round(float(recall[0]), 4),
        "bertscore_f1": round(float(f1[0]), 4),
    }


def novel_ngram_ratio(candidate: str, article: str, n: int) -> float:
    candidate_ngrams = ngrams(tokenize(candidate), n)
    article_ngrams = set(ngrams(tokenize(article), n))
    if not candidate_ngrams:
        return 0.0
    novel = sum(1 for gram in candidate_ngrams if gram not in article_ngrams)
    return novel / len(candidate_ngrams)


def compression_ratio(candidate: str, article: str) -> float:
    candidate_tokens = tokenize(candidate)
    article_tokens = tokenize(article)
    if not article_tokens:
        return 0.0
    return len(candidate_tokens) / len(article_tokens)


def extract_fact_spans(text: str) -> set[str]:
    spans = {match.group(0).strip().lower() for match in NUMERIC_FACT_PATTERN.finditer(text)}
    spans.update(match.group(0).strip().lower() for match in ENTITY_PATTERN.finditer(text))
    return {span for span in spans if span}


def grounding_score(candidate: str, article: str) -> float:
    facts = extract_fact_spans(candidate)
    if not facts:
        return 1.0

    article_lower = article.lower()
    supported = sum(1 for fact in facts if fact in article_lower)
    return supported / len(facts)


def non_redundancy_score(candidate: str) -> float:
    candidate_bigrams = ngrams(tokenize(candidate), 2)
    if not candidate_bigrams:
        return 1.0

    counts = Counter(candidate_bigrams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return max(0.0, 1.0 - (repeated / len(candidate_bigrams)))


def length_score(candidate: str, article: str) -> float:
    ratio = compression_ratio(candidate, article)
    if 0.08 <= ratio <= 0.3:
        return 1.0
    if ratio < 0.08:
        return max(0.0, ratio / 0.08)
    return max(0.0, 1.0 - ((ratio - 0.3) / 0.3))


def compute_rule_based_scores(candidate: str, article: str) -> dict[str, float]:
    ratio = compression_ratio(candidate, article)
    grounding = grounding_score(candidate, article)
    redundancy = non_redundancy_score(candidate)
    length_fit = length_score(candidate, article)
    overall = (grounding + redundancy + length_fit) / 3

    return {
        "novel_1gram_ratio": round(novel_ngram_ratio(candidate, article, 1), 4),
        "novel_2gram_ratio": round(novel_ngram_ratio(candidate, article, 2), 4),
        "compression_ratio": round(ratio, 4),
        "grounding_score": round(grounding, 4),
        "non_redundancy_score": round(redundancy, 4),
        "length_score": round(length_fit, 4),
        "rule_based_quality": round(overall, 4),
    }


def compute_summary_metrics(candidate: str, reference: str, article: str) -> dict[str, float]:
    bert_scores = compute_bert_scores(candidate, reference)
    rule_scores = compute_rule_based_scores(candidate, article)
    return {**bert_scores, **rule_scores}


def average_scores(score_rows: list[dict[str, float]]) -> dict[str, float]:
    if not score_rows:
        return {key: 0.0 for key in METRIC_KEYS}

    keys = score_rows[0].keys()
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
