from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


METRICS = ("rouge1", "rouge2", "rougeL")


def load_results(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_bar_chart(metric: str, aggregate_scores: dict[str, dict[str, float]], output_dir: Path) -> None:
    modes = list(aggregate_scores.keys())
    values = [aggregate_scores[mode][metric] for mode in modes]

    plt.figure(figsize=(7, 4))
    bars = plt.bar(modes, values)
    plt.title(f"{metric.upper()} by Prompt Strategy")
    plt.xlabel("Prompt Mode")
    plt.ylabel("Score")
    plt.ylim(0, max(values + [0.1]) + 0.1)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_dir / f"{metric}.png", dpi=200)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot ROUGE results from a JSON file.")
    parser.add_argument("--results", default="sample_results.json", help="Path to results JSON.")
    parser.add_argument("--output-dir", default="charts", help="Directory for generated charts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_results(results_path)
    aggregate_scores = payload["aggregate_scores"]
    for metric in METRICS:
        save_bar_chart(metric, aggregate_scores, output_dir)

    print(f"Saved charts to {output_dir}")


if __name__ == "__main__":
    main()
