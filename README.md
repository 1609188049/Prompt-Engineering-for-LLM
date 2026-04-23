# Prompt Engineering for LLM: Summarization Quality

This project is a CS439 final project scaffold for studying how prompting strategies affect summarization quality on news articles.

We compare:

- `zero-shot`
- `few-shot`
- `cot` (chain-of-thought style prompting)

The codebase supports:

- loading a small news summarization dataset
- generating summaries for multiple prompt modes
- computing ROUGE-style metrics
- exporting results to JSON
- plotting comparison charts
- calling an API to test prompt modes interactively

## Project Structure

```text
.
├── README.md
├── experiment_plan.md
├── prompts.py
├── evaluate.py
├── run_experiments.py
├── plot_results.py
├── api.py
├── example_dataset.json
├── sample_results.json
└── requirements.txt
```

## Quick Start

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the experiment pipeline with the mock backend:

```bash
python3 run_experiments.py --dataset example_dataset.json --output results.json --backend mock
```

3. Generate plots:

```bash
python3 plot_results.py --results results.json --output-dir charts
```

4. Start the API:

```bash
uvicorn api:app --reload
```

## API Overview

The API exists so you can test different prompting modes without running the whole experiment loop.

### `GET /health`

Basic health check.

### `GET /modes`

Returns the supported prompt modes.

### `POST /prompt-preview`

Builds the final prompt for a given article and mode.

Request body:

```json
{
  "mode": "few-shot",
  "article": "Your article text here.",
  "target_sentences": 3
}
```

### `POST /summarize`

Generates a summary using the selected prompt strategy.

Request body:

```json
{
  "mode": "cot",
  "article": "Your article text here.",
  "target_sentences": 3,
  "backend": "mock"
}
```

### `POST /evaluate`

Generates summaries for all modes on one article and returns per-mode ROUGE scores against a reference summary.

Request body:

```json
{
  "article": "Your article text here.",
  "reference_summary": "Ground truth summary here.",
  "backend": "mock"
}
```

## Backends

Two backends are supported:

- `mock`: deterministic local summary generation for testing the pipeline and API
- `openai`: real LLM generation using `OPENAI_API_KEY`

To use the OpenAI backend:

```bash
export OPENAI_API_KEY=your_key_here
python3 run_experiments.py --backend openai
```

## Example Research Workflow

1. Pick 50 to 100 articles from a news summarization dataset.
2. Run each article through `zero-shot`, `few-shot`, and `cot`.
3. Compute ROUGE-1, ROUGE-2, and ROUGE-L.
4. Compare average scores.
5. Discuss whether prompting style affects summary quality.

## Notes

- The included dataset is intentionally small and only for demonstration.
- The mock backend is for local testing, not final experimental claims.
- For the final project, replace the sample dataset with a larger real news dataset.
