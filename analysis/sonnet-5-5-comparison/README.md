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

## Results (2026-10-03 run)

Ran all three configs locally for the 4 postseason games on 2026-10-03 (network/API keys worked fine locally, unlike the cloud session). Outputs are the `.md`/`-run.txt` files in this directory. Code was fully reverted after - no switch has been made.

- **Metrics:** all 12 calls (4 games x 3 configs) returned `stop_reason: end_turn`, 1 web search each, no `max_tokens` truncation. Average description length was similar across configs: Sonnet 5 medium 1175 chars, Sonnet 5.5 low 1056 chars, Sonnet 5.5 medium 1148 chars.
- **Thinking tokens:** Sonnet 5 used some real thinking (0-419 tokens per call, varied). Sonnet 5.5 used **zero** thinking tokens in all 4 games at both low and medium effort. So the "notes drop into thinking blocks" risk noted above doesn't appear to be what's happening here - nothing was silently dropped, since there was no thinking at all.
- **Quality - the real difference:** Sonnet 5's descriptions are one flowing, connected paragraph per game, weaving stats and storylines together. Sonnet 5.5's descriptions consistently split into a short bolded lead sentence followed by several short, choppy, disconnected declarative sentences/paragraphs (e.g. "Milwaukee went 103-59 and 55-26 at home." / "Robbie Ray's 0.63 pNERD is the weak spot."). This happened at both low and medium effort, across all 4 games - it reads like a fact sheet rather than a written piece, and lost most of the wit. Net impression: not ready to switch as-is.

Best guess at cause: not a bug or dropped content (thinking tokens were 0), but a genuine style difference - Sonnet 5.5 is choosing to write terser, more declarative sentences at a given nominal effort level (consistent with Anthropic's note that effort levels were recalibrated between 5 and 5.5). Newer model generations often optimize for benchmarks like coding/agentic tool-use/instruction-following rather than narrative prose quality, so "newer and usually better" doesn't necessarily transfer to this kind of writing task.

## Prompt tweak ideas (not yet applied)

The current prompt (`src/mlb_watchability/prompt-game-summary-template.md`) bans bullets/emojis/sections and says "keep it to sentences" and "witty and wry," but never explicitly requires one connected paragraph - Sonnet 5 happened to interpret the existing instructions that way, Sonnet 5.5 is satisfying them literally with short, isolated sentences instead. "Witty and wry" is also vague enough that each model fills it in differently - goal is concise and well-written, not so wry it reads funny, like something from a site that prioritizes good writing.

Two ideas to try, in order of expected impact, before deciding whether to switch models:

1. Add an explicit single-paragraph/connective-prose instruction, e.g.: "Write the summary as one connected paragraph, not a string of short, standalone facts - link ideas with transitions ('but', 'which is why', 'meanwhile') so stats and storylines read as a narrative, not a list."
2. Add one concrete example of the desired tone, pulled from a Sonnet 5 output here that reads well (a short excerpt, not a full game). A few-shot anchor is probably the most reliable lever for style - it narrows the ambiguity in "witty and wry" that's letting each model drift to its own default, without having to enumerate every forbidden adjective.

Holding off on more adjective-banning (the prompt already has a decent list) - that's diminishing returns and risks blander writing, the opposite of the goal.

Next step, if these are worth trying: draft the template edit (including picking a good excerpt from one of the 2026-10-03 Sonnet 5 outputs as the example), then re-run the Sonnet 5.5 comparison to see if it closes the gap.
