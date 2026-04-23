from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

from evaluate import average_scores, compute_rouge_scores
from prompts import SUPPORTED_MODES, build_prompt


@dataclass
class SummaryRequest:
    article: str
    mode: str
    target_sentences: int = 3
    backend: str = "mock"


OPENAI_COMPATIBLE_BACKENDS = {"openai", "deepseek", "claude"}
BACKEND_CHOICES = ("mock", "openai", "gemini", "deepseek", "claude")


def normalize_text_output(text: str) -> str:
    return text.strip()


def split_sentences(text: str) -> list[str]:
    chunks = [part.strip() for part in text.replace("\n", " ").split(".")]
    return [chunk for chunk in chunks if chunk]


def compress_sentence(sentence: str, max_words: int = 12) -> str:
    tokens = sentence.split()
    trimmed = tokens[:max_words]
    return " ".join(trimmed).strip(",;: ")


def mock_generate_summary(article: str, mode: str, target_sentences: int = 3) -> str:
    sentences = split_sentences(article)
    if not sentences:
        return ""

    if mode == "zero-shot":
        selected = sentences[:target_sentences]
    elif mode == "few-shot":
        selected = [compress_sentence(sentence, max_words=11) for sentence in sentences[:target_sentences]]
    elif mode == "cot":
        ordered = []
        if sentences:
            ordered.append(sentences[0])
        if len(sentences) > 2:
            ordered.append(sentences[-1])
        if len(sentences) > 1:
            ordered.append(sentences[1])
        selected = [compress_sentence(sentence, max_words=14) for sentence in ordered[:target_sentences]]
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return ". ".join(item.rstrip(". ") for item in selected if item).strip() + "."


def openai_compatible_generate_summary(prompt: str, model: str, backend: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI package is not installed. Run `pip install -r requirements.txt`.") from exc

    if backend == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None
    elif backend == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = "https://api.deepseek.com"
    elif backend == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = "https://api.anthropic.com/v1/"
    else:
        raise ValueError(f"Unsupported OpenAI-compatible backend: {backend}")

    if not api_key:
        env_var = {
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
        }[backend]
        raise RuntimeError(f"{env_var} is not set.")

    client = OpenAI(api_key=api_key, base_url=base_url)
    if backend == "claude":
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return normalize_text_output(response.choices[0].message.content or "")

    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return normalize_text_output(response.output_text)


def gemini_generate_summary(prompt: str, model: str) -> str:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed. Run `pip install -r requirements.txt`.") from exc

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return normalize_text_output(response.text or "")


def generate_summary(request: SummaryRequest, model: str = "gpt-4.1-mini") -> dict[str, str]:
    prompt = build_prompt(request.mode, request.article, request.target_sentences)
    if request.backend == "mock":
        summary = mock_generate_summary(request.article, request.mode, request.target_sentences)
    elif request.backend in OPENAI_COMPATIBLE_BACKENDS:
        summary = openai_compatible_generate_summary(prompt, model=model, backend=request.backend)
    elif request.backend == "gemini":
        summary = gemini_generate_summary(prompt, model=model)
    else:
        raise ValueError(f"Unsupported backend: {request.backend}")

    return {
        "mode": request.mode,
        "backend": request.backend,
        "prompt": prompt,
        "summary": summary,
    }


def load_dataset(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and "records" in payload:
        return payload["records"]
    return payload


def run_experiment(
    dataset_path: Path,
    output_path: Path,
    backend: str,
    target_sentences: int,
    model: str,
    modes: tuple[str, ...],
) -> dict:
    dataset = load_dataset(dataset_path)
    records = []
    mode_scores: dict[str, list[dict[str, float]]] = {mode: [] for mode in modes}

    for item in dataset:
        article_id = item["id"]
        article = item["article"]
        reference = item["reference_summary"]
        mode_outputs = {}

        for mode in modes:
            response = generate_summary(
                SummaryRequest(
                    article=article,
                    mode=mode,
                    target_sentences=target_sentences,
                    backend=backend,
                ),
                model=model,
            )
            scores = compute_rouge_scores(response["summary"], reference)
            mode_scores[mode].append(scores)
            mode_outputs[mode] = {
                "summary": response["summary"],
                "scores": scores,
            }

        records.append(
            {
                "id": article_id,
                "reference_summary": reference,
                "results": mode_outputs,
            }
        )

    aggregate = {mode: average_scores(scores) for mode, scores in mode_scores.items()}
    payload = {
        "metadata": {
            "dataset": str(dataset_path),
            "backend": backend,
            "target_sentences": target_sentences,
            "model": model if backend != "mock" else "mock-summarizer",
            "num_articles": len(dataset),
            "modes": list(modes),
        },
        "aggregate_scores": aggregate,
        "articles": records,
    }

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run summarization prompt experiments.")
    parser.add_argument("--dataset", default="example_dataset.json", help="Path to dataset JSON file.")
    parser.add_argument("--output", default="results.json", help="Path to output JSON file.")
    parser.add_argument("--backend", default="mock", choices=BACKEND_CHOICES, help="Summary backend.")
    parser.add_argument("--target-sentences", type=int, default=3, help="Desired summary length.")
    parser.add_argument("--model", default="gpt-4.1-mini", help="Model name for the selected backend.")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=SUPPORTED_MODES,
        default=list(SUPPORTED_MODES),
        help="Prompt modes to evaluate. Fewer modes reduce API calls.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_experiment(
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
        backend=args.backend,
        target_sentences=args.target_sentences,
        model=args.model,
        modes=tuple(args.modes),
    )
    print(json.dumps(result["aggregate_scores"], indent=2))


if __name__ == "__main__":
    main()
