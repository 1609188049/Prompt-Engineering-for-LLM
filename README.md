# Prompt Engineering for LLM: Summarization Quality

This project is a CS439 final project scaffold for studying how prompting strategies affect summarization quality on news articles.

We compare:

- `zero-shot`
- `few-shot`
- `cot` (chain-of-thought style prompting)

The codebase supports:

- loading a small news summarization dataset
- generating summaries for multiple prompt modes
- computing semantic and rule-based summary metrics
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
├── prepare_kaggle_dataset.py
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

Generates summaries for all modes on one article and returns per-mode evaluation scores against a reference summary.

Request body:

```json
{
  "article": "Your article text here.",
  "reference_summary": "Ground truth summary here.",
  "backend": "mock"
}
```

## Backends

Five backends are supported:

- `mock`: deterministic local summary generation for testing the pipeline and API
- `openai`: real LLM generation using `OPENAI_API_KEY`
- `gemini`: real LLM generation using `GEMINI_API_KEY`
- `deepseek`: real LLM generation using `DEEPSEEK_API_KEY`
- `claude`: real LLM generation using `ANTHROPIC_API_KEY`

To use a real-model backend:

```bash
export OPENAI_API_KEY=your_key_here
python3 run_experiments.py --backend openai --model gpt-4.1-mini

export GEMINI_API_KEY=your_key_here
python3 run_experiments.py --backend gemini --model gemini-2.5-flash

export DEEPSEEK_API_KEY=your_key_here
python3 run_experiments.py --backend deepseek --model deepseek-chat

export ANTHROPIC_API_KEY=your_key_here
python3 run_experiments.py --backend claude --model claude-3-5-sonnet-latest
```

Notes:

- The `claude` backend uses Anthropic's OpenAI SDK compatibility layer.
- The `deepseek` backend uses DeepSeek's OpenAI-compatible API.
- You can reduce API usage by limiting prompt modes, for example: `--modes zero-shot few-shot`

## Kaggle Dataset Workflow

To reproduce the Kaggle-based experiment sample used in this repository:

```bash
python3 prepare_kaggle_dataset.py \
  --output result/kaggle_sample_dataset.json \
  --sample-size 24

python3 run_experiments.py \
  --dataset result/kaggle_sample_dataset.json \
  --output result/kaggle_mock_results.json \
  --backend mock \
  --modes zero-shot few-shot cot

MPLCONFIGDIR=/tmp/matplotlib python3 plot_results.py \
  --results result/kaggle_mock_results.json \
  --output-dir result/charts
```

Notes:

- The Kaggle sample script uses `description` as a weak reference summary proxy.
- The sample is filtered toward English-language records with longer article bodies.
- By default, each run randomly samples 24 articles and records the generated seed in the output metadata.
- You can optionally add `--max-per-source N` if you want a stricter source-balance constraint.
- `24 articles x 3 modes = 72 model calls`, which is usually a good tradeoff between cost and a still-readable comparison.

### Lower-Cost Real-Model Run

If you want a cheaper first pass before running the full 3-mode comparison:

```bash
export GEMINI_API_KEY=your_key_here

python3 prepare_kaggle_dataset.py \
  --output result/kaggle_sample_dataset.json \
  --sample-size 24

python3 run_experiments.py \
  --dataset result/kaggle_sample_dataset.json \
  --output result/kaggle_gemini_results.json \
  --backend gemini \
  --model gemini-2.5-flash \
  --modes zero-shot few-shot
```

This 2-mode run makes only `48` API calls and is a good budget-friendly smoke test before running all three prompt strategies.

## Evaluation Metrics

The current evaluation stack combines semantic similarity and rule-based diagnostics:

- `bertscore_precision`, `bertscore_recall`, `bertscore_f1`: semantic similarity against the reference summary using BERTScore
- `novel_1gram_ratio`, `novel_2gram_ratio`: how much of the summary uses n-grams not copied directly from the source article
- `compression_ratio`: summary token count divided by source article token count
- `grounding_score`: rule-based check for whether numbers and capitalized entity spans in the summary also appear in the source article
- `non_redundancy_score`: penalty for repeated summary bigrams
- `length_score`: heuristic preference for concise summary lengths
- `rule_based_quality`: average of `grounding_score`, `non_redundancy_score`, and `length_score`

Notes:

- BERTScore is the primary semantic similarity metric in this project.
- The first BERTScore run may download a local encoder model, so evaluation is heavier than the lightweight lexical metrics used in simpler baselines.
- You can override the encoder with `BERTSCORE_MODEL`, for example `export BERTSCORE_MODEL=roberta-large`.

## Example Research Workflow

1. Pick 50 to 100 articles from a news summarization dataset.
2. Run each article through `zero-shot`, `few-shot`, and `cot`.
3. Compute BERTScore and the rule-based summary diagnostics.
4. Compare average scores.
5. Discuss whether prompting style affects summary quality.

## Notes

- The included dataset is intentionally small and only for demonstration.
- The mock backend is for local testing, not final experimental claims.
- For the final project, replace the sample dataset with a larger real news dataset.
