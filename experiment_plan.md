# Experiment Plan

## Main Experiment

Research question:

Do different prompting strategies significantly affect the quality of LLM-generated summaries?

### Prompt strategies

- `zero-shot`: direct summarization with no examples
- `few-shot`: summarization after showing example article-summary pairs
- `cot`: guided reasoning before final summary generation

### Dataset

Recommended datasets:

- CNN / DailyMail
- BBC News
- Kaggle News datasets

Initial scope:

- 50 to 100 articles
- one human reference summary per article

### Evaluation

Use:

- ROUGE-1
- ROUGE-2
- ROUGE-L

Report:

- per-article scores
- average scores by mode
- charts comparing prompt strategies

## Bonus Experiment 1: Summary Length

Question:

Does target summary length change how much prompting strategy matters?

Compare:

- 1 sentence
- 3 sentences
- 5 sentences

Design:

- keep the same articles and model
- vary only `target_sentences`
- compare ROUGE changes across prompt modes

Expected value:

- shorter summaries may reward concise prompting
- longer summaries may benefit more from structured reasoning

## Bonus Experiment 2: Prompt Wording

Question:

Does wording style affect output quality even within the same prompt strategy?

Compare:

- `Summarize the article.`
- `Write a concise and informative summary.`
- `Write a factual summary using clear news style.`

Design:

- use one fixed mode at a time
- keep article set, model, and output length constant
- compare average ROUGE results

Expected value:

- some wording may produce more complete or more concise summaries
- prompt wording effects may be smaller than few-shot examples but still measurable
