# Research index — evidence-first-trading (2026-11-16)

## What exists and how trustworthy it is

| # | File | Origin | Status |
|---|------|--------|--------|
| 02 | 02-papers.md | main agent this session, **web-verified** (Baltussen, Zarattini, SEBI) | usable |
| 03 | 03-validation.md | background free agent (openrouter/thinkingmachines/inkling-2-small:free); 396 lines, URLs on every claim, DSR/PBO/WFA/MinTRL/Kelly/bug checklist + 12-step pre-registration | usable (agent-produced, spot-check formulas before teaching them) |
| 04 | 04-cost-survival.md | background free agent (nemotron-3.5-lightning); 470 lines, venue fee tables & leverage math; **free-tier limit hit post-write; unverified** | leads only |
| 00 | this index | main agent | n/a |

## What is missing (agents errored on free-tier limits)

| 01 | architecture.md | every free model exhausted | MISSING |
| 05 | strategy-catalog.md | ling-3.2-flash agent — unresolved at push time | MISSING |
| 06 | filters.md | failed | MISSING |
| 07 | price-factors.md | failed | MISSING |
| 08 | quant-trends.md | failed | MISSING |
| 09 | psych.md | failed | MISSING |

## What the battery established instead (strongest artifact)

`evaluation/PRE-REGISTER.md` (frozen pre-run) + `scripts/backtest_battery.py` + `evaluation/battery-results.md`:
**16 pre-registered candidates, 0 survive 10bp costs.** Not an agent claim — reproducible with one command.

## Reading order
1. 02-papers.md — why the literature does not rescue day-trading alpha
2. evaluation/battery-results.md — our own 16 nulls
3. references/failure-modes.md (8a/8b)
4. 03-validation.md — how to pre-register and test any candidate properly
5. 04-cost-survival.md — venue-by-venue fee math (verify numbers)
