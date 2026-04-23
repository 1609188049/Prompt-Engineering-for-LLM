from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

import kagglehub
import pandas as pd


DEFAULT_HANDLE = "everydaycodings/global-news-dataset"
DEFAULT_FILE = "data.csv"
TRUNCATION_PATTERN = re.compile(r"\s*\[\+\d+\s+chars\]\s*$")


def clean_article_text(text: str) -> str:
    cleaned = TRUNCATION_PATTERN.sub("", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def ascii_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(ord(char) < 128 for char in text) / len(text)


def resolve_cached_dataset_dir(handle: str) -> Path | None:
    owner, slug = handle.split("/", maxsplit=1)
    versions_root = Path.home() / ".cache" / "kagglehub" / "datasets" / owner / slug / "versions"
    if not versions_root.exists():
        return None
    version_dirs = sorted(
        [path for path in versions_root.iterdir() if path.is_dir()],
        key=lambda path: path.name,
    )
    if not version_dirs:
        return None
    return version_dirs[-1]


def load_kaggle_dataframe(handle: str, file_name: str) -> pd.DataFrame:
    dataset_dir = resolve_cached_dataset_dir(handle)
    if dataset_dir is None:
        dataset_dir = Path(kagglehub.dataset_download(handle))
    csv_path = dataset_dir / file_name
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find {file_name} in {dataset_dir}")
    return pd.read_csv(csv_path)


def build_experiment_dataset(
    df: pd.DataFrame,
    sample_size: int,
    random_seed: int | None,
    max_per_source: int | None,
) -> list[dict[str, str]]:
    article_text = df["full_content"].fillna(df["content"]).fillna("").map(clean_article_text)
    reference_text = df["description"].fillna("").map(clean_article_text)

    filtered = df.copy()
    filtered["article"] = article_text
    filtered["reference_summary"] = reference_text
    filtered["ascii_ratio"] = filtered["article"].map(ascii_ratio)

    filtered = filtered[
        filtered["reference_summary"].str.len().between(60, 400)
        & filtered["article"].str.len().between(800, 6000)
        & (filtered["ascii_ratio"] >= 0.98)
    ].copy()

    filtered = filtered.drop_duplicates(subset=["title", "reference_summary"])
    filtered = filtered.sample(frac=1.0, random_state=random_seed)
    if max_per_source is not None:
        filtered = filtered.groupby("source_name", dropna=False, group_keys=False).head(max_per_source)
    filtered = filtered.head(sample_size)

    records = []
    for row in filtered.itertuples(index=False):
        records.append(
            {
                "id": f"kaggle-{row.article_id}",
                "article": row.article,
                "reference_summary": row.reference_summary,
                "title": row.title,
                "category": row.category,
                "source_name": row.source_name,
                "published_at": str(row.published_at),
                "dataset_handle": DEFAULT_HANDLE,
            }
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a Kaggle news dataset sample for summarization experiments.")
    parser.add_argument("--handle", default=DEFAULT_HANDLE, help="Kaggle dataset handle.")
    parser.add_argument("--file-name", default=DEFAULT_FILE, help="Dataset file to load from the Kaggle package.")
    parser.add_argument("--output", default="result/kaggle_sample_dataset.json", help="Output JSON path.")
    parser.add_argument("--sample-size", type=int, default=24, help="Number of examples to sample.")
    parser.add_argument("--seed", type=int, help="Optional random seed for reproducible sampling.")
    parser.add_argument("--max-per-source", type=int, help="Optional maximum number of sampled rows per source.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dataframe = load_kaggle_dataframe(args.handle, args.file_name)
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 10**9)

    dataset = build_experiment_dataset(
        dataframe,
        sample_size=args.sample_size,
        random_seed=seed,
        max_per_source=args.max_per_source,
    )

    metadata = {
        "dataset_handle": args.handle,
        "file_name": args.file_name,
        "sample_size": len(dataset),
        "seed": seed,
        "max_per_source": args.max_per_source,
        "reference_summary_note": "reference_summary uses the Kaggle description field as a weak summary proxy.",
    }

    payload = {
        "metadata": metadata,
        "records": dataset,
    }

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
