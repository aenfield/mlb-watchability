# Sonnet 5.5 comparison

Handoff notes for comparing the daily job's game descriptions on the current model against Claude Sonnet 5.5 at two effort levels, before deciding whether to switch. Started in a Claude Code cloud session on 2026-10-03; the runs couldn't happen there (the network policy blocked `statsapi.mlb.com`, and no API keys were set), so they're meant to be picked up locally.

## Current state (nothing changed yet)

- The scheduled GitHub run (`.github/workflows/daily-markdown.yml`, cron `24 13 * * *`) uses the input defaults: `--game-desc-source llm --game-desc-limit 30 --llm-model normal --llm-model-provider anthropic`, with `ENABLE_LLM_RETRIES=true`.
- `normal` + `anthropic` maps to `ANTHROPIC_MODEL_FULL` (`create_llm_client` in `src/mlb_watchability/llm_client.py`), currently `"claude-sonnet-5"`.
- `AnthropicParams.effort` is `"medium"`; `max_tokens` falls back to 3000; web search tool is `web_search_20250305` with no `max_uses`.

## Plan

Do all three runs back to back on the same date so games and stats match (web search results will still vary between runs). Use `.env` for `ANTHROPIC_API_KEY` and `SCRAPE_DO_API_KEY`.

For each run, from the repo root:

```bash
ENABLE_LLM_RETRIES=true uv run mlbw-markdown --game-desc-source llm --game-desc-limit 30 \
  --llm-model normal --llm-model-provider anthropic 2>&1 | tee run.txt
```

Then move the generated markdown file and `run.txt` into this directory with a suffix (logs are saved as `.txt` because `*.log` is gitignored):

| Run | Code state | Output names |
|---|---|---|
| 1 | Unchanged (Sonnet 5, effort `medium`) | `<date>-sonnet-5-medium.md`, `<date>-sonnet-5-medium-run.txt` |
| 2 | `ANTHROPIC_MODEL_FULL = "claude-sonnet-5-5"`, `AnthropicParams.effort = "low"` | `<date>-sonnet-5-5-low.md`, `<date>-sonnet-5-5-low-run.txt` |
| 3 | `ANTHROPIC_MODEL_FULL = "claude-sonnet-5-5"`, `AnthropicParams.effort = "medium"` | `<date>-sonnet-5-5-medium.md`, `<date>-sonnet-5-5-medium-run.txt` |

After run 3, revert the code changes until a winner is chosen. When making the real change, follow red/green TDD: first add a test asserting `create_llm_client(provider="anthropic", model="normal")` resolves to `"claude-sonnet-5-5"`, see it fail, then change the constant.

## What to compare

- Summary quality and length across the three `.md` files.
- From the run logs: `stop_reason`, `input_tokens`, `output_tokens`, `thinking_tokens`, and `web_search_requests` per game. Watch for `max_tokens` stops - thinking shares the 3000-token budget with the summary.

## Notes on Sonnet 5.5

- Same price as Sonnet 5 ($2 / $10 per MTok input / output) and same tokenizer.
- None of its breaking changes affect this code: the code never sends `thinking: disabled`, forced `tool_choice`, assistant prefill, or `temperature`. `ANTHROPIC_MODELS_SUPPORTING_ADAPTIVE_THINKING` is built from `ANTHROPIC_MODEL_FULL`, so adaptive thinking and `output_config.effort` keep being sent.
- Effort levels are recalibrated; `medium` on 5.5 isn't the same amount of thinking as `medium` on 5. Anthropic's suggested starting point for content generation and search is `low`.
- Text the model writes between tool calls (e.g. "Let me search for...") comes back as `text` blocks on Sonnet 5, and the code concatenates every block with `.text` into the description. On 5.5, notes longer than a sentence or two come back as `thinking` blocks instead, so they drop out of the summary.
- More refusal categories (`stop_reason: "refusal"`, five `stop_details` categories); unlikely for baseball summaries.
- Comments mentioning "Sonnet 5" in `llm_client.py` (around the request-params comment) and `tests/test_llm_client.py` should be updated with the switch.

## Later, as a separate change: `web_search_20260209`

The newer web search version adds dynamic filtering (the model runs code to filter results before they enter its context; no beta header, no separate `code_execution` tool). Input tokens per call (22K-150K) are dominated by search results, so this could cut cost. Before switching, check: new code-execution result blocks don't leak text into descriptions, `web_sources` extraction still works, `pause_turn` stop reasons (not handled today), consider a `max_uses` cap, and confirm current pricing.
