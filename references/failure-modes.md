# Failure modes — check this before every plan and every backtest review

## 1. Look-ahead & repainting (the SMC trap)
- A swing high defined as "bar higher than N bars each side" **cannot be confirmed until N bars later.** Indicators that draw levels at the pivot bar use information that did not exist -> "beautiful equity curves and they fail immediately in live trading" [S31].
- Same-bar execution: signal computed from bar close but filled at bar open/low.
- Full-sample preprocessing (normalize/scale/impute on train+test together).
- Fix: bar-close signal -> next-bar fill; confirm pivots with delay; purged CV + embargo.

## 2. Multiple testing / overfitting
- **False Strategy Theorem:** no Sharpe threshold rejects a false strategy given enough trials [S26]. "Not reporting the number of trials … is a similar kind of fraud" (Bailey et al. 2014) [S26].
- **Backtest Sharpe -> OOS: R² < 0.025** across 888 Quantopian algorithms; more backtests run = wider gap [S27].
- 215 bank-promoted strategies: median **73% Sharpe decline** backtest->live [S35].
- Fix: log every trial; Deflated Sharpe; PBO/CSCV; parameter plateaus not peaks; untouched holdout.

## 3. Costs
- Barber et al. 2009: aggregate retail drag **3.8 pp/yr**, virtually all from aggressive orders; institutions *gained* from trading in the same market [S2].
- Novy-Marx & Velikov: "in all cases transaction costs reduce the strategies' profitability and its associated statistical significance" [S3].
- Fix: slippage sweep (0/5/10/20/50bp), worst-case spread crossing, worst-case baseline.

## 4. LLM-specific failure modes
- Unattended LLM trading: "it misreads one number with total confidence, and that mistake becomes a live order with nobody watching" [S28].
- Agents don't reliably follow the user's strategy (107-trade month, -1%, strategy not actually applied) [S28].
- TradingAgents (112K stars) reproduction: 15.8-18.1% vs 19.1% buy-and-hold; had future-news leakage bugs [S28].
- LLM-discovered "edges": a backtest that improves the metric "is, by default, overfit, look-ahead, a multiple-comparisons artifact, cost-free, or market drift wearing a strategy" [S26a].
- Fix: this skill's rails — deterministic Python for all math, citations required, paper-first, human confirmation phrase.

## 5. Negative skew / steamroller
- 80% WR at -1R losses: E = 0.8(0.3) - 0.2(1.0) = +0.04R pre-cost; tail events cluster in gaps [S34].
- Option-seller / LTCM precedent: years of small wins, one catastrophic loss [S35].

## 6. Survivorship & selection
- Published track records exclude blowups and deleted instruments.
- Community profitability claims: 1-10% persistently profitable (peer-reviewed), >85% lose over multi-year windows (regulators) [S9][S2].
- NASAA: one trade out of 100 made 93% of profit in a 26-account sample [S9].

## 7. Behavioral
- Disposition effect: realize winners 1.5-2.4x more than losers [S2]; traders overcount skill because profitable-day share is inflated (54% observed vs 48% counterfactual) [S2].
- Overtrading dose-response: most-active quintile 11.4% vs 18.5% net [S2]. **The skill's scanning frequency should be a guardrail, not a stimulus.**

## 8a. Registered-null-trials (pre-registered battery — do not trade these)
Our own pre-registered 16-trial battery (`evaluation/PRE-REGISTER.md`, results in
`evaluation/battery-results.md`) failed at 10bp costs across the board. Anyone
presenting these with zero costs and tiny stops is quoting the artifact:
- **Gap-and-go**: 39.0% WR, -0.082R gross, **-0.815R @ 10bp** (n=4,284; p<0.0001).
- **PDH/PDL breakout continuation**: 30.0% WR, -0.193R gross (n=683; p<0.0001).
- **PDH/PDL first-touch fade / other tight-stop fades**: positive gross WR (59.2%) but degenerate short risk (stop bp << spread) -> **-12.7R @ 10bp**. Artifact, not edge.
- **Lunch-hour reversion**: +0.002R gross, -1.045R @ 10bp (n=1,314).
- **Opening-drive fade**: 14.8% WR, -3.418R @ 10bp (n=438; p<0.0001).
- Fix: before proposing any day-trade rule, ask "what's the stop distance in bp? Which battery row did it die in?"

## 8b. Degenerate-stop artifact (new failure mode — cost of recognising tiny stops)
A stop placed a few basis points from entry makes R-multiples look spectacular
and simultaneously makes costs *multiply*: netR = grossR - bp / risk_bp.
Never accept any backtest where the median stop distance is < ~15bp of price
without re-running with a minimum stop floor as an amendment.

## 9. Tool defaults that lie
- TradingView: zero commission, zero slippage, instant limit fills, repainting-invalid backtests [S38].
- MT4/5 modeling-quality gaps; cross-engine divergence bugs (double-charged commissions, silent truncation) [S39].
- Fix: verify engine assumptions; vectorized for screening -> event-driven for final validation [S40].
