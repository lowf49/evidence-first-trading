# Setup Catalog — evidence-graded

Rules are stated precisely enough to implement in `scripts/setup_scanner.py` and `scripts/backtest_orb.py`.
Every entry ends with a citation id pointing to `citations.md`.

---

## TIER A — peer-reviewed + independent backtest

### A1. Opening Range Breakout (15-min)
- **Rules:** At 09:45 ET (US cash session) form OR_high/OR_low = max/min of 09:30–09:45 5-min highs/lows. Trigger = first 5-min bar **close** beyond OR_high (long) or OR_low (short). Stop = opposite side of the OR. Target = 2R (R = OR width) or session end, whichever first. No re-entry after stop-out. Max one trade/day/instrument.
- **Stats:** 5-min OR captures median 20% of day's range; 77–80% of day's range undetermined at OR close (n=3,034 ES/NQ days, 2014–2026 [S11]). 30-min OR + 5-min close confirmation: 70.7% continuation (7/10 days) [S11]. Independent 1,178,668-trade test: 5-min WR 53.78%, 30-min 49.38%, 15-min 46% with highest EV/trade [S12]. Zarattini & Aziz: QQQ 5-min ORB 2016–23 +1,484% vs +169% (33% annualized net of commissions; uses 3× leveraged ETFs; "optimized" variant ignores slippage) [S13]. Pre-2026 academic version positive on Swedish/index data [S14].
- **Failure modes:** extremely sensitive to range/stop/target rules; slippage must be swept — one replication found 66.7% WR needed to break even [S12].
- **Works in:** US equities/ETFs, ES/NQ, claimed for crypto (session-anchored variant); regime: trend-leaning sessions.

### A2. Prior Day High/Low (PDH/PDL) reaction
- **Rules:** Levels = previous regular-session high/low. Statistic of interest: touch/no-touch of each level and reaction (first touch + 5-min close back inside). Frequency of a *level hit* (not a directional edge): NQ 89.5%, ES 90.8% touch ≥1 of PDH/PDL; both levels swept only 10.1–10.6% of sessions; slight high-side bias (55.2% NQ / 56.5% ES reach high first) [S15].
- **Evidence:** multiple independent backtests + academic support for resting-limit-order clustering at reference levels (Kavajecz & Odders-White 2004 [S16]; Bourghelle & Cellier 2007) and Osler's stop-cluster evidence (stops cluster just beyond such levels) [S5].
- **Failure modes:** "hit rate of a touch" ≠ directional expectancy; the reaction trade itself is Tier B (no peer-reviewed edge published for the entry rule).

### A3. Intraday momentum — first half → last 30 minutes
- **Rules:** Directional component: sign of rest-of-day return (09:30–15:30) predicts final 30-min return sign; NQ adj. R² 4.10% in-sample, 3.76% OOS; directional accuracy 53–56% [S17]. Also overnight-to-RTH continuation for volatility sizing (53.7% continuation, rank corr 0.55 with remaining range) [S18].
- **Evidence:** Baltussen, Lammers & Martens (2021), 45-year study, 60+ futures across equities/bonds/commodities/currencies — JFE-tier [S17].
- **Failure modes:** 53–56% is a thin edge — costs dominate if traded flat; use as context/filter, not standalone.

### A4. Round-number clustering
- **Rules:** informational: price levels cluster at round numbers (BTC: 2.05× expected clustering; terminal digit 0 appears 1.8× expected) [S19][S20][S21]. Bars: magnetic attraction is weak (1.6% asymmetry) — treat round numbers as *liquidity/stop locations*, not magnets.
- **Use:** stop placement, target placement, and identifying where Osler-type stop cascades originate [S5].

---

## TIER B — independent backtest only

### B1. Lunch-hour lull (12:00–13:30 ET)
Reversion edge retention 44.4% during lunch vs 54–64% otherwise; volume −30% (12:00–14:00) [S22][S23]. Use as a **filter** (expect weaker follow-through, tighter ranges), not a signal.

### B2. Opening volatility U-curve
ES 5-min ATR 6–8 pts at open → 2–3 midday → 5–7 close; 35–40% of daily range in first and last 60 min [S24][S6]. Use for: cost awareness (impact ~5× at open [S1]) and sizing.

### B3. VWAP band position (descriptive)
Price inside ±1σ 44.7%, ±2σ 86.1% of time; first daily touch reverts to VWAP by EOD ~97.6% (Asia 95%, London 78%, NY only 30%) [S25]. Descriptive statistics — see D1 for the trading-rule version.

---

## TIER C — LORE (label on sight)

- **9/20 EMA pullback / cross** — no published win rate exists; breakeven WR at 1.8R = 35.7%, so claimed win rates are unverifiable without n and R [S8].
- **Support/resistance flips as taught** — Park & Irwin: >half of TA studies positive but many ignored costs; no consistently documented academic S/R entry rule [S8].
- **Candlestick patterns as taught** (doji/hammer/engulfing standalone) — no independently verified win rates from the retail framing [S8][S30].
- **Gap-and-go / gap fade** — no specific academic hit-rate study located; gap-fill stats vary wildly by instrument [S8].
- **ICT/SMC: order blocks, fair value gaps, kill zones** — no peer-reviewed quantitative study; common implementations are look-ahead-biased (swing levels drawn at pivot bar, confirmed N bars later) and repaint [S8][S31]. The clean, testable subset (liquidity sweep: `Low < priorLow AND Close > priorLow`) remains unvalidated [S31].

## TIER D — DEBUNKED (refuse with explanation)

- **D1. VWAP mean reversion as a generic rule** — BTC: −8.45% (3mo), −32.9% (15mo), PF 0.73 in both windows ("consistently negative, not unlucky"); 4,360 SPY backtests: best survivor didn't beat buy-and-hold [S8].
- **D2. Retail attention following** — top Robinhood-bought stocks −4.7%/20d (JF 2022) [S9]; WSB long/short no alpha (FMPM 2022).
- **D3. "Simple MA rules beat mature markets net of costs"** — Hsu, Kuan & Newey (White's Reality Check/SPA): profitable simple rules only in young markets, not DJIA/S&P 500 [S10].
- **D4. Unattended LLM signal trading** — see failure-modes.md §4 [S26][S27][S28].
