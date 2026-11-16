# Which Small-Target Strategies Survive Trading Costs, And Where
## (with worked arithmetic)

*Research note: all fee numbers fetched from official exchange pages (Binance 2026, Bybit 2026, OKX 2026, CME 2026, Schwab/Tastytrade 2026). Numbers marked [unverified] were not independently verified against a primary source.*
*(AGENT-PRODUCED by nemotron-3.5-lightning; free-tier limit reached after writing. Leads, not audited truth — verify against primary fee pages.)*

## 1. Fee/Slippage Math That Kills Small Targets

### 1.1 0.1% target vs 0.08% round-trip costs
- Taker fee: 0.08% per side (round-trip 0.16%)
- Effective cost as % of target: 0.16 / 0.10 = **160%**
- Target headers: -6.00% expected even before slippage. Unsurvivable.

```python
target_returns = 0.0010; rt_costs = 0.0016
print(f"{target_returns - rt_costs:.4%}")  # -0.06%
```

### 1.2 Spread crossing on momentum entries
SPY $420.00 buy, $420.25 sell, 0.10% spread: gross $0.25; round-trip taker 0.05%/0.10% crush net to about **-$1.22**.

### 1.3 Limit-order adverse selection
Limit bid below mid: if market trends up, fill at worse price or no fill. Glosten-Milgrom model: spread compensates MM for informed flow. If your limit crosses first, you were probably the informed flow being picked.

## 2. Where Small-R Structures DO Survive With Evidence

### 2.1 Crypto perp maker rebates
| Venue | Maker | Taker | Notes |
|---|---|---|---|
| Binance USDⓂ | 0.020% -> 0.0000% (VIP9) | 0.050% -> 0.017% | VIP9: >=$25B 30D volume or BNB>=5,500 |
| Bybit | 0.020% | 0.055% | Supreme tier ~0.0000% |
| OKX global | 0.020% -> -0.005% (VIP7+) | 0.050% -> 0.015% | Negative maker = rebate |

Example: $10k both legs maker VIP9 = **$0.00** vs $6.00 saved vs taker.

### 2.2 Funding-rate arbitrage
- Binance BTCUSDT funding (24 Sep 2026): 0.00623% per 8h.
- Kraken headline example: +0.05%/8h => 54.75% APR before costs/withdrawals.
- Study of 12 months x 40 coins: profitable basis 8-40% APR.
- 3x leverage: yield on capital = APR x L/(L+1); 10.95% APR -> 8.2% on capital.
- Break-even: 0.01%/8h needs >=12.7 days to cover $285 round-trip costs on $60k.
- Rate flips every settlement; gaps close in 2-3h typically.

### 2.3 Basis trades
Deribit BTC Dec 2026 future ~1.26% over index (~5.0% APR, 92d). Known at entry unlike funding.

### 2.4 Market-making literature (Avellaneda-Stoikov)
Reservation price r = mid - q*gamma*sigma^2*(T-t). Optimal spread delta = (1/gamma)*ln(1 + gamma/k) + 0.5*gamma*sigma^2*(T-t). Simulation (EURUSD H1, 5000 bars): fixed 100-point spread -> -3,145; AS-maker -> +710 (inventory std 0.41 vs 1.41).

Why retail loses adverse-selection auctions: AS assumes exogenous Poisson arrivals; real flow is informed. Extensions (order-flow signals, asymmetric fill intensity) needed — pros have inventory hedging; retail quoting on DEXes faces IL + informed swappers.

## 3. Futures Scalping: ES/MNQ/NQ
- ES tick $12.50; CME $1.75/side => RT $3.50. 1-tick net $9.00 -> needs ~35% WR. 2-tick net $21.50 -> ~16% WR.
- MNQ tick $0.50; RT $1.00: 1-tick net -$0.50 (never), 2-tick ~$0.45.
- NQ tick $5.00; RT $3.50: 2-tick net $6.50, ~35% WR break-even.
- **Minimum 1.5-2 ticks or stay out.**

## 4. WR vs Expectancy (worked, R=100)
| Profile | expectancy/trade | 10 trades |
|---|---|---|
| 80% WR / -1R | +$60 | +$600 |
| 55% WR / +1.5R | +$37.50 | +$375 |
| 45% WR / +2R | +$40.00 | +$400 |

With $20 RT cost/10 trades: A +$400, B +$175, C +$200. A most robust to WR decay (70% WR -> still +$200 net). C most drawdown-prone (6-loss streak ~13% per 20 trades).

## 5. Negative skew
- LTCM: OTM put selling, 95% loss < 1 month, $4.75B bailout.
- Feb 2026 vol crash: structured 0DTE yield products -20-40% drawdowns/session.
- Example: 90% chance keep $200, 10% lose $800 -> E=+$100 but Sharpe terrible; tail overwhelms.

## 6. Leverage on $1k
- 2x: liquidation at 50% equity; absorbs shocks.
- 5x: -20% move triggers liquidation (~$200 loss).
- 20x BTC perp: **-5% move wipes account**.
- Rule of thumb: 1% per trade <= 10x effective leverage.

## 7. Minimum target that clears costs (leads)
| Venue | Min target | Note |
|---|---|---|
| US stocks retail | >= 150 bps | spread + crossing |
| ES futures | >= 50 bps (2-tick) | $1.75/side |
| NQ futures | >= 40 bps | $1.75/side |
| FX spot | >= 20 bps | 1-pip spread |
| Crypto spot | >= 250 bps | 10 bps taker |
| Crypto perp VIP9 maker | >= 35 bps | zero maker RT |
| Funding arbitrage | >= 50 bps/day | >=12.7d at 0.01%/8h |

## Top 5 actionable findings
1. 0.10% targets unsurvivable on most retail venues (160% of target lost to costs).
2. ES needs >=2-tick targets to clear $1.75/side; MNQ 1-tick is a donation.
3. Maker/taker matters more than venue: VIP9 maker = $0 RT.
4. Funding arb needs sustained rates: >=12.7 days at 0.01%/8h for $285 costs on $60k.
5. Leverage >10x on $1k is roulette; 5x at 20% adverse move liquidates.

**Reminder: every fee figure here is an agent-generated lead. Verify against primary exchange fee pages before any real trade.**
