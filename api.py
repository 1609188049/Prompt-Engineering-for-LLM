from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from evaluate import compute_summary_metrics
from prompts import SUPPORTED_MODES, build_prompt
from run_experiments import SummaryRequest, generate_summary


app = FastAPI(
    title="Prompt Strategy Summarization API",
    description="API for testing summarization prompt modes and comparing outputs.",
    version="1.0.0",
)


class PromptPreviewRequest(BaseModel):
    mode: str = Field(..., description="Prompt strategy to preview.")
    article: str = Field(..., description="Article text to summarize.")
    target_sentences: int = Field(default=3, ge=1, le=10)


class SummarizeRequest(PromptPreviewRequest):
    backend: str = Field(default="mock", pattern="^(mock|openai|gemini|deepseek|claude)$")
    model: str = Field(default="gpt-4.1-mini")


class EvaluateRequest(BaseModel):
    article: str
    reference_summary: str
    target_sentences: int = Field(default=3, ge=1, le=10)
    backend: str = Field(default="mock", pattern="^(mock|openai|gemini|deepseek|claude)$")
    model: str = Field(default="gpt-4.1-mini")


def ensure_mode(mode: str) -> None:
    if mode not in SUPPORTED_MODES:
        raise HTTPException(status_code=400, detail=f"Unsupported mode: {mode}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/modes")
def list_modes() -> dict:
    return {"supported_modes": SUPPORTED_MODES}


@app.post("/prompt-preview")
def prompt_preview(payload: PromptPreviewRequest) -> dict:
    ensure_mode(payload.mode)
    return {
        "mode": payload.mode,
        "target_sentences": payload.target_sentences,
        "prompt": build_prompt(payload.mode, payload.article, payload.target_sentences),
    }


@app.post("/summarize")
def summarize(payload: SummarizeRequest) -> dict:
    ensure_mode(payload.mode)
    try:
        result = generate_summary(
            SummaryRequest(
                article=payload.article,
                mode=payload.mode,
                target_sentences=payload.target_sentences,
                backend=payload.backend,
            ),
            model=payload.model,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "mode": result["mode"],
        "backend": result["backend"],
        "target_sentences": payload.target_sentences,
        "prompt": result["prompt"],
        "summary": result["summary"],
    }


@app.post("/evaluate")
def evaluate_article(payload: EvaluateRequest) -> dict:
    all_results = {}

    for mode in SUPPORTED_MODES:
        try:
            result = generate_summary(
                SummaryRequest(
                    article=payload.article,
                    mode=mode,
                    target_sentences=payload.target_sentences,
                    backend=payload.backend,
                ),
                model=payload.model,
            )
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        all_results[mode] = {
            "summary": result["summary"],
            "scores": compute_summary_metrics(result["summary"], payload.reference_summary, payload.article),
        }

    return {
        "backend": payload.backend,
        "target_sentences": payload.target_sentences,
        "results": all_results,
    }
