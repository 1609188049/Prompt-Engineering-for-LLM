from __future__ import annotations

from typing import Callable


SUPPORTED_MODES = ("zero-shot", "few-shot", "cot")


FEW_SHOT_EXAMPLES = [
    {
        "article": (
            "City officials announced a new public bus route connecting two "
            "underserved neighborhoods. The plan is expected to reduce commute "
            "times and improve access to local jobs and schools."
        ),
        "summary": (
            "City officials introduced a new bus route linking underserved "
            "neighborhoods. The route aims to shorten commute times and improve "
            "access to jobs and schools."
        ),
    },
    {
        "article": (
            "Researchers at a university developed a low-cost water filter for "
            "rural communities. Early tests showed the design removed most "
            "harmful particles while remaining easy to maintain."
        ),
        "summary": (
            "University researchers created an affordable water filter for rural "
            "areas. Early testing showed strong particle removal and simple "
            "maintenance."
        ),
    },
]


def build_zero_shot_prompt(article: str, target_sentences: int = 3) -> str:
    return (
        f"Summarize the following news article in {target_sentences} sentences.\n\n"
        f"Article:\n{article}\n"
    )


def build_few_shot_prompt(article: str, target_sentences: int = 3) -> str:
    examples = []
    for index, example in enumerate(FEW_SHOT_EXAMPLES, start=1):
        examples.append(
            f"Example {index}:\n"
            f"Article: {example['article']}\n"
            f"Summary: {example['summary']}\n"
        )
    joined_examples = "\n".join(examples)
    return (
        f"{joined_examples}\n"
        f"Now summarize the following news article in {target_sentences} sentences.\n\n"
        f"Article:\n{article}\n"
    )


def build_cot_prompt(article: str, target_sentences: int = 3) -> str:
    return (
        "Read the following news article.\n"
        "First identify the main event, key actors, and most important outcome.\n"
        f"Then write a clear {target_sentences}-sentence summary based on that analysis.\n\n"
        f"Article:\n{article}\n"
    )


PROMPT_BUILDERS: dict[str, Callable[[str, int], str]] = {
    "zero-shot": build_zero_shot_prompt,
    "few-shot": build_few_shot_prompt,
    "cot": build_cot_prompt,
}


def build_prompt(mode: str, article: str, target_sentences: int = 3) -> str:
    if mode not in PROMPT_BUILDERS:
        raise ValueError(f"Unsupported mode: {mode}")
    return PROMPT_BUILDERS[mode](article, target_sentences)
