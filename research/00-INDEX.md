# Research index — evidence-first-trading (2026-11-16)

## What exists and how trustworthy it is

| # | File | Origin | Status |
|---|------|--------|--------|
| 02 | 02-papers.md | main agent this session, **web-verified** (Baltussen, Zarattini, SEBI) | usable |
| 04 | 04-cost-survival.md | background free agent (nemotron-3.5-lightning); 470 lines with exchange-fee tables & worked math; **agent hit free-tier limit after writing; unverified, treat as leads** | usable with caution, numbers need primary re-check |
| 00 | this index | main agent | n/a |

## What is missing (agents errored on free-tier limits)

| 01 | architecture.md | attempted 3 times on different free models — all failed | MISSING |
| 03 | validation.md (quant validation) | attempted 2 times — failed | MISSING (Deflated-Sharpe/MinTRL math lives in failure-modes.md partially; see also references/cost-math.md) |
| 05 | strategy-catalog.md | agent led (ling-3.2-flash) — unresolved at push time | MISSING |
| 06 | filters.md | failed (2 models) | MISSING |
| 07 | price-factors.md | failed | MISSING |
| 08 | quant-trends.md | failed | MISSING |
| 09 | psych.md | failed | MISSING |

Blocking cause (logged verbatim for each):
- opencode free (mimo, hy4, flint, longcat, beam, iceman, deepseek, super-vl, glm-5.3): "Free usage limit reached."
- opencode-go (hy4, longcat, beam, iceman): requires OpenCode Go subscription; iceman: training-data consent; longcat: region not allowed.
- OpenRouter free (ling-3.2, gemma-4-26b/31b, nemotron-super/ultra, north-mini-code, particle-1, flint-v1, ernie, nano-omni, lfm-3.2, inkling-2-small): "Rate limit exceeded: free-models-per-day."
- Groq: 8,000-token TPM cap vs ~9.6k harness request; Llama 3.3-70b ran but output truncated by network/DNS block.
- Cerebras: HTTP 402 payment required.

## What the battery established instead (strongest artifact)

`evaluation/PRE-REGISTER.md` (frozen pre-run) + `scripts/backtest_battery.py` + `evaluation/battery-results.md`:
**16 pre-registered candidates, 0 survive 10bp costs.** Not an agent claim — reproducible with one command.

## Reading order
1. 02-papers.md (why the literature does not rescue day-trading alpha)
2. evaluation/battery-results.md (our own 16 nulls)
3. references/failure-modes.md (8a/8b — the two failure modes this session added)
4. 04-cost-survival.md (venue-by-venue fee math; verify numbers)
