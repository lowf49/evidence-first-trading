# Validation results

## Part 1 — Deterministic historical backtest (`python scripts/backtest_orb.py`, run 2026-11-16)

Window: 12 instruments (SPY QQQ IWM DIA AAPL NVDA TSLA MSFT AMD META AMZN GLD),
5m bars ≤60d for intraday parts, 10y daily for level stats. Data: Yahoo Finance.

### A1 — Opening Range Breakout (exact catalog rules, n=166 trades)
| Metric | Result |
|---|---|
| Win rate | **47.6%** (LONG 42.4% n=85, SHORT 53.1% n=81) |
| Expectancy @ 0bp slippage | **+0.088R** (positive) |
| @ 5bp | +0.006R (marginal) |
| @ 10bp | **−0.076R (NEGATIVE)** |
| @ 20bp | −0.240R |
| @ 50bp | −0.732R |

**Verdict: the skill's own Tier-A setup fails its own slippage sweep at 10bp —
exactly what the research predicted (ORB is cost-critical).** The skill would
flag this as FRAGILE, not tradeable without cost advantage.

### A2 — PDH/PDL touch statistics (n=30,156 sessions, 10y, 12 symbols)
| Stat | Result | Vendor claim |
|---|---|---|
| Touch ≥1 prior-day level | **75.6%** | 89–91% (index futures) |
| Touch both | **8.8%** | ~10% (index futures) |
| Touch PDH | 45.2% | — |
| Touch PDL | 39.2% | — |

Honest divergence: single-stock/ETF touch rates run ~13pp below the vendor
index-futures numbers. Both-sweeps figure matches. The skill records its own
number over the vendor's.

### A3 — Last-30-min momentum (n=718 sessions)
Sign accuracy **40.9%** — below chance in this 60-day window vs Baltussen et al.'s
53–56% (45-year study). Recorded as NOT confirmed in this sample; the skill's
catalog entry notes the short-window failure.

## Part 2 — Blind LLM evaluation (see this directory)

Built `cases.json` (381 cases, 228 tradeable, 3 canaries), masked symbols,
%-only features, post-cutoff Oct–Nov 2026 data. Conditions: {gemma, nemotron} ×
{skill excerpt, no skill} vs baselines (always-long, seeded random, pure rule).
Scoring: `python evaluation/blind_eval.py score` → `score_report.json`.
