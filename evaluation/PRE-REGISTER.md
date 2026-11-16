# PRE-REGISTRATION — Day-trading candidate battery
*Written and frozen 2026-11-16T07:20 PT, BEFORE any new backtest runs. Any variant added after this point is an "amendment" and increments the trial count.*

## Universe & data

| Set | Data | Window | Notes |
|-----|------|--------|-------|
| W5m | 5m bars | last 60d (Yahoo cap), 22 symbols | recent/out-of-time vs 60m |
| W60m | 60m bars | last 730d (Yahoo cap), 22 symbols + BTC-USD + ETH-USD | older window = robustness; first 60d excluded from W60m for C1/A1b-style recency logic |
| W1d | 1d bars | last 10y, 22 symbols | daily strategies |

Symbols (identical to A1): SPY, QQQ, IWM, DIA, AAPL, NVDA, TSLA, MSFT, AMD, META, AMZN, GLD, NFLX, JPM, XOM, UNH, COST, DIS, BA, INTC, MU, TLT.

## Candidates (pre-registered, bar-close signals only)

| ID | Name | Exact rule | Data set(s) | Trials |
|----|------|------------|-------------|--------|
| C1 | ORB-15 strict | First 15-min range (3 5m bars); trigger = close of bar starting at 09:45; direction = close vs range hi/lo; stop = opposite edge; target = 2R; exit = target/stop/EOD | W5m, W60m (first bar as "OR", second bar close as trigger, older window only) | 2 |
| C2 | PDH breakout continuation | If session trades above prior-day-high during 10:30-16:00 **and** prior-day-hi was *not* touched in first 15m: LONG at 10:30 close; stop = PDH; target = 2R; else SHORT per symmetric rule vs PDL | W5m, W60m | 2 |
| C3 | PDH/PDL first-touch fade | If price first-touches PDH in sessions 09:30-12:00: SHORT at that bar close; stop = PDH + 0.1xprev range; target = session open; EOD exit. Mirror for PDL | W5m, W60m | 2 |
| C4 | Gap-and-go | Gap >= +0.5% vs prior close; if 09:45 15m close >= session open: LONG; stop = session open; target = 2R; EOD. Mirror gap-down SHORT (Gap-and-go down). | W5m, W60m (confirm = first-bar close vs open) | 2 |
| C5 | Gap fade | Same gap trigger, but fade: LONG->SHORT reversal if 15m close breaks back below/above open; stop = extreme of first 15m; target = gap body midpoint (open); EOD | W5m, W60m | 2 |
| C6 | Opening-drive fade | |close09:45 - prevClose| >= 0.6 x prev-day range -> fade: SHORT if up-drive, LONG if down-drive; stop = 15m high/low; target = session open; EOD | W5m | 1 |
| C7 | Lunch reversion | Morning return (09:30->12:00) r; if r > 0 -> SHORT at 12:00 close; if r < 0 -> LONG; stop = morning extreme; exit = 13:30 close (fixed time, no target) | W5m | 1 |
| C8 | First-hour continuation | Direction = sign(close10:30 - open09:30); enter at 10:30 close; stop = opposite extreme of first 60m; target = 2R; EOD | W60m | 1 |
| C9 | Last-30-min momentum FADE | Direction = **against** sign(close15:30 - open09:30); enter at 15:30 close; stop = extreme of 14:30-15:30 bar opposite side; exit = 16:00 close (fixed time) | W60m older window only (A3 was measured on W5m recent — no overlap) | 1 |
| C11 | NR7 breakout | Signal day = 7-day-lowest trading range; next day: if close > signal high -> LONG at that close, stop = signal low; if close < signal low -> SHORT; exit next day's close; max 1 day hold after entry | W1d | 1 |
| C12 | Strong/weak close drift | Signal: prior-day close in top 20% of prior-day range -> LONG next day open->close; bottom 20% -> SHORT | W1d | 1 |
| C13 | Crypto 4h reversal | BTC-USD + ETH-USD, 60m bars: if 4-bar return >= +1% -> SHORT; <= -1% -> LONG; exit after 4 bars; one position at a time per symbol | W60m | 1 |
| C15 | Cross-sectional RS | Daily, rank 22-symbol universe by prior-day % change; LONG quartile 1, SHORT quartile 4; enter next-day open, exit same-day close; risk = median prior-day range | W1d | 1 |

**Total pre-registered trials N = 16** (window-runs counted separately; LONG/SHORT splits are reporting, not selection).

## Cost model

- Report 0 / 5 / 10 / 20 / 50 bp (slippage + half-spread per side, in bp of notional) for every candidate.
- **Primary verdict at 10bp.** Any positive result at 0bp that dies at 10bp is labelled FRAGILE (same rule as A1).
- Crypto (C13) additionally reported at 4bp (typical maker rebate offset) and 10bp.

## Metrics (per candidate, per data set)

1. n (trades; C15: n = days with both legs, returns in R using median-range risk)
2. Win rate (R > 0) with Wilson 95% CI
3. Expectancy @ each cost level (mean netR), t-stat = mean / (stdev/sqrt(n)), 2-tailed p (normal approx, valid n >= 100)
4. Profit factor = sumwins / |sumlosses|
5. Max drawdown in R (cumulative sequence)
6. **Sub-period sign check**: median date splits the window into 2 halves; candidate PASSES only if expectancy sign is the same in both halves (not magnitude, sign only)
7. Deflated interpretation: with N = 16 trials, primary-claim threshold = t-stat corresponding to p < 0.05 / 16 ~= 0.0031 (|t| ~= 2.96)

## Success criteria (frozen — cannot be relaxed after seeing results)

Candidate **passes** only if ALL hold:

1. Expectancy @ 10bp > 0 AND normal-approx 95% CI excludes 0
2. Sign consistent across both sub-periods
3. n >= 100 (else labelled UNDERPOWERED — no claim allowed)
4. |t| >= 2.96 (Bonferroni for N=16)

A candidate that fails any criterion is reported as-is. **No parameter may be retuned on these data sets.** A retuned variant = amendment, N -> 17+, and must be disclosed as such.

## Excluded (with reason)

- ICT/SMC, 9/20 EMA, VWAP-mean-reversion — no publishable rules or no peer-reviewed evidence; folklore.
- Round-number reactions — no implementable rule from OHLCV alone without tick data.
- Candlestick patterns — sub-coin-flip accuracy in prior tests; adds trials without adding evidence.
- Funding-rate crypto edge — Yahoo provides no funding rates; requires an authenticated exchange API; out of scope for keyless validation.

## Amendment log

None yet. Any change logged here before its backtest runs.
