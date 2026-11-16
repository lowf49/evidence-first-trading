---
name: evidence-first-trading
description: Evidence-graded day-trading decision support. Scans for recurring setups (opening range breakout, prior-day levels, intraday momentum), computes net-of-cost expectancy, audits backtests for overfitting, and journals trades. Use when the user asks to scan setups, verify a trading strategy's evidence, plan a trade, review a backtest, or journal/review trades. Never auto-executes. Not financial advice.
---

# Evidence-First Trading

Decision support for day traders. Every claim carries an evidence grade and a citation.
**This skill never predicts, never says "will", and never places an order without explicit human confirmation.**

## Evidence tiers (defined in `references/evidence-rubric.md`)

| Tier | Meaning | Action |
|---|---|---|
| **A** | Peer-reviewed + independent backtest | May drive `/trade-plan` |
| **B** | Independent backtest only | May drive `/trade-plan` with sample-size warning |
| **C** | Forum/vendor lore, untested | Labelled "LORE — unvalidated"; informational only |
| **D** | Backtested and debunked | Refused; explain the negative result |

## Workflows

### 1. `/setup-scan <watchlist>`
Run `python scripts/setup_scanner.py --symbols SPY,QQQ,... --days 5`.
Report only Tier A/B triggers: setup name, exact trigger values, historical frequency (from `references/setup-catalog.md`), evidence grade, source. Show Tier C hits greyed as LORE. Never phrase output as a prediction — output is "trigger fired; historically occurred X% of sessions (n=…, source)".

### 2. `/verify-setup <description>`
Look up the setup in `references/setup-catalog.md`.
- Found → return tier, precise rules, sample sizes, known failure modes, citation.
- Not found → label **FORUM-LORE (not in catalog)** and search `references/failure-modes.md` for analogous debunked patterns.

### 3. `trade-plan <idea>` (mandatory before any trade)
1. Identify tier of the setup (must be A or B to continue).
2. Compute expectancy — requires ALL of: win rate (with n), avg win R, avg loss R, commission, spread, slippage. If any cost input is missing, **stop and ask**.
   `python scripts/expectancy_calc.py --wr 0.55 --winR 1.2 --lossR 1.0 --costR 0.15`
3. Cost breakeven check: `python scripts/cost_breakeven.py --list`
4. Sample-size gate: <30 historical occurrences = REJECT; 30–199 = WARN; ≥200 across ≥2 regimes = PASS.
5. Fill `templates/trade-plan.md`, including the mandatory base-rate footer.

### 4. `/backtest-review <file or code>`
Audit for, in order:
1. Look-ahead: bar-close signal → next-bar fill? Levels drawn from same bar? Repainting indicators (a common SMC failure)?
2. Costs: zero commission/slippage defaults (TradingView default!)? Run slippage sweep mentally: does edge survive 10bp?
3. Trial accounting: how many parameter variants were tried? Undisclosed trials = invalid.
4. Survivorship: delisted names included?
5. Sample: ≥200 trades across bull/bear/high-vol regimes?
Output `templates/backtest-review.md` with PASS/FAIL per item. Reference `references/failure-modes.md`.

### 5. `/market-state <symbol>`
Descriptive facts only (U-shape position, opening-range status, PDH/PDL distance, round-number proximity, VWAP band position). No direction.

### 6. `/journal` and `/review`
`python scripts/journal.py add|summary`. Weekly review must show: actual vs claimed win rate (Wilson interval), R distribution, max consecutive losses, negative-skew warning (many small wins + rare large loss = the steamroller pattern in `references/failure-modes.md`).

## Safety rails (non-negotiable)
- **Paper-first**: any broker integration defaults to paper (Alpaca/Kraken paper). Live orders require the exact phrase `CONFIRM LIVE ORDER` from the human.
- **Banned words**: guaranteed, will (future), certain, high-probability without n. Preferred phrasing: "historically occurred X% of the time (n=…, source)".
- **Every number cites** `references/citations.md`.
- **Base-rate footer** on every trade plan: "Base rate: ~1–10% of day traders are persistently profitable; 87–97% of retail derivatives/day traders lose net of costs (Barber et al. 2014; Chague et al. 2020; SEBI 2026)."
- **No API keys stored in skill files.** Data via keyless sources (Yahoo chart API) or user-provided env vars.

## File map
- `references/setup-catalog.md` — Tier A–D setups with exact rules + citations
- `references/cost-math.md` — breakeven tables, expectancy math, slippage sweeps
- `references/evidence-rubric.md` — how tiers are assigned
- `references/market-structure.md` — what actually moves price (OFI, stop cascades, U-shape)
- `references/failure-modes.md` — overfitting, negative skew, survivorship, debunked setups
- `references/citations.md` — full source list
- `scripts/` — deterministic Python (scanner, expectancy, cost, journal, backtest, blind eval)
- `templates/` — trade plan, backtest review, post-mortem
- `evaluation/blind_eval.py` — blind out-of-sample evaluation harness

**Disclaimer: educational decision support. Not financial advice. No prediction of future prices is made or implied.**
