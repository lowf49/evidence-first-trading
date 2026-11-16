# Cost math & breakeven tables

## Expectancy

```
Expectancy($/trade) = wr × avgWin − (1−wr) × avgLoss
Expectancy(R)       = wr × winR − (1−wr) × lossR
Breakeven WR        = 1 / (1 + R)          # R = winR/lossR ratio
# R = 1.8 → breakeven WR = 35.7%; R = 1.0 → 50%; R = 0.5 → 66.7%
```
`scripts/expectancy_calc.py` implements this **net of costs** and refuses to run without fee/spread/slippage inputs.

## Cost as fraction of a small target (round-trip)

| Market | Typical round-trip cost | Verdict for 0.2–0.5% targets |
|---|---|---|
| US stock/ETF (commission-free) | spread ~0.05–0.1% implicit | ⚠️ spread alone eats a 0.2% target meaningfully |
| US stock (PDT, <$25k: ≤3 day-trades/5 sessions) | + pattern-day-trading constraint | regulatory barrier by design |
| ES futures (1 tick = 0.25 pt ≈ $12.50; ~$1.25–2.40/side commission) | ~0.04–0.08% per RT at typical size | viable only with tight ticks |
| FX retail | 2–5 pips + commission ≈ 0.02–0.05% | marginal |
| Crypto spot taker | 0.04–0.1% per side (0.08–0.2% RT) | ❌ taker scalping loses |
| Crypto perp **maker** | 0–0.02% + rebates on some venues | ✅ only structural retail niche |

Sources: [S2][S3][S32][S33] in citations.md. Numbers are order-of-magnitude; re-measure with your own fills.

## Slippage sweep (mandatory)

Run backtest at 0 / 5 / 10 / 20 / 50 bp slippage. **If the edge dies at 10 bp, there is no edge** [S4].
Worst-case baseline: buy at ask, sell at bid for every fill.
r/algotrading practitioner rule: switch from mid-price fills to spread-crossing → ~half of strategies stop being profitable [S4].

## Why small-R/high-WR systems fail (worked example)

80% WR, win +0.3R, loss −1.0R:
`E = 0.8(0.3) − 0.2(1.0) = +0.04R` — **before costs**; one adverse-spread event (slip 0.3R on both sides) → E ≈ 0. Then the 20% tail clusters in gaps/locks (loss > 1R). This is the negative-skew "pennies vs steamroller" profile [S34][S35].

## Kelly / optimal f for high-WR systems

Full Kelly `f* = (p·b − q)/b` with small b (edge per trade small) → f* small; **half-Kelly or less** because (a) variance of estimated p is high at n<200, (b) negative skew violates Kelly's assumptions, (c) over-Kelly at 80% WR systems produces drawdowns larger than the edge justifies [S36].
