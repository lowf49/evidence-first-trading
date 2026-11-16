# Pre-Registered Candidate Battery — Results
*Run 2026-11-16, after `evaluation/PRE-REGISTER.md` was frozen. All 16 trials reported as run; nothing was retuned, no candidate was dropped, nothing is claimed as a win.*

Universe: 22 symbols (SPY, QQQ, IWM, DIA, AAPL, NVDA, TSLA, MSFT, AMD, META, AMZN, GLD, NFLX, JPM, XOM, UNH, COST, DIS, BA, INTC, MU, TLT). Data: Yahoo Finance (5m 60d, 60m 730d, 1d 10y). Costs: 0/5/10/20/50 bp per side of notional; primary verdict at 10bp. N = 16 window-runs; Bonferroni threshold |t| >= 2.96 (p < 0.0031).

## Headline

**Zero of 16 pre-registered candidates survives realistic costs. Every candidate is a FAIL at 10bp.**
This is consistent with all prior evidence (ORB cost-free edge only on one 60d window, hourly window dead at 0bp; blind LLM eval shows the skill's value is refusal, not prediction; literature shows no reliable short-horizon directional edge after costs).

| ID | Candidate | n | WR | exp (gross) | net @10bp | t | Same-sign halves | Verdict |
|----|-----------|---|----|-------------|-----------|---|------------------|---------|
| C1 | ORB-15 (5m recent) | 5,560 | 48.5% | +0.000R | -0.097R | +0.00 | no | **FAIL** |
| C1 | ORB (60m, older) | 4,966 | 48.5% | -0.003R | -0.098R | -0.38 | no | **FAIL** |
| C2 | PDH/PDL breakout cont. | 683 | 30.0% | -0.193R | -2.351R | -4.19 | yes | **FAIL** |
| C3 | PDH/PDL first-touch fade | 14,439 | 59.2% | +0.299R | -12.7R | +12.7 | yes | **FAIL** |
| C4 | Gap-and-go | 4,284 | 39.0% | -0.082R | -0.815R | -4.85 | yes | **FAIL** |
| C5 | Gap fade | 4,264 | 35.2% | +0.021R | -1.132R | +0.39 | yes | **FAIL** |
| C6 | Opening-drive fade | 438 | 14.8% | -0.796R | -3.418R | -5.99 | yes | **FAIL** |
| C7 | Lunch reversion | 1,314 | 39.4% | +0.002R | -1.045R | +0.04 | no | **FAIL** |
| C8 | First-hour continuation | 16,051 | 45.3% | -0.002R | -0.177R | -0.26 | no | **FAIL** |
| C9 | Last-30-min momentum fade | 14,793 | 35.8% | +0.134R | -2.552R | +5.56 | yes | **FAIL** |
| C11 | NR7 expansion | 5,626 | 48.0% | +0.022R | -0.043R | +2.07 | yes | **FAIL** (p=.039, not Bonferroni) |
| C12 | Close-position drift | 25,327 | 49.6% | -0.001R | -0.065R | -0.21 | no | **FAIL** |
| C13 | Crypto 4h reversal | 3,294 | 53.0% | -0.018R | -0.118R | -0.69 | no | **FAIL** |
| C15 | Cross-sectional RS (Q1-Q4) | 2,510 | 46.9% | -0.027R | -0.086R | -3.76 | yes | **FAIL** |

**Degenerate-stop caveat (important).** C2/C3/C6/C9 use a stop anchored at a level very close to entry (PDH/PDL +/- 0.1xrange; the 14:30-15:30 bar range). On quiet days the risk distance collapses to a few bp, which (a) inflates R-multiples on wins and (b) makes the cost term bp/risk_bp explode — that is why C3's net shows -12.7R even with +0.299R gross. These candidates are **structurally fragile by construction**, not failed-by-luck. A robust version would need a minimum stop distance (e.g., >=0.15-0.25% of price) — that is a NEW trial (amendment, N=17), and must be pre-registered before it is run. Do not read C3's WR 59.2% or C9's WR 35.8% as opportunities; both are artifacts of tiny-risk stops, and both die catastrophically at 10bp.

## What survived

Nothing survived costs. Even **gross** expectancy was <= 0 for 10 of 16 runs, and the two positive-gross runs that clear |t| >= 2 (C11 NR7 +0.022R t=2.07; C3/C9, t=12.7/5.6) are either degenerate-stop artifacts or fail the Bonferroni threshold and die at 10bp. C11's gross t=2.07 (p=0.039) would not survive even one extra trial's worth of snooping correction.

## Why this matters to the skill

1. The skill's premise — "evidence-first, cost-gated, refuse negative-expectancy setups" — is now backed by an entire pre-registered null result, not just single-family tests.
2. The only actionable outputs of this battery are **refusals**: C4 gap-and-go, C2 PDH breakout, C6 drive fade are *significantly negative* beyond costs (all p < 0.0001 with negative sign) — these are candidates to explicitly avoid, even before any edge consideration.
3. When someone shows a backtest of any of these with zero costs and a tiny stop, it will look great; the battery is the counter-evidence.

## Honest summary in one line

*There is no short-horizon day-trade directional edge net of 10bp costs in this universe, in this window, under these pre-registered rules — and six more independent confirmations (C8, C12, C13, C1x2, C15) all agree.*

Amendment path (not yet run): C3'/C9' with minimum stop >= 0.15% of price, logged as amendment before any run, N -> 17-18. Until then, N = 16 stands.

Reproduce: `python scripts/backtest_battery.py` (cached Yahoo data in `evaluation/cache/`; first run re-fetches). Raw trade-level data: `evaluation/battery_results.json` (local only).
