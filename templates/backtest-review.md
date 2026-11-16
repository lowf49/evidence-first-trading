# Backtest review — {{strategy}} ({{date}})

## 1. Look-ahead / validity
- [ ] Bar-close signal → next-bar fill (no same-bar execution)
- [ ] Levels/pivots confirmed with N-bar delay (no pivot-bar drawing)
- [ ] No repainting indicators
- [ ] No full-sample preprocessing (scaling/imputation fit on train only)
- **Result:** {{PASS/FAIL}} — {{notes}}

## 2. Costs
- [ ] Commission + spread + slippage all present (TradingView defaults to ZERO — check)
- [ ] Slippage sweep: 0/5/10/20/50 bp → expectancy {{...}}
- [ ] Worst-case baseline (buy ask / sell bid)
- **Result:** {{PASS/FAIL}} — survives 10bp? {{yes/no}}

## 3. Trial accounting
- [ ] Number of parameter variants tried: {{n}} (undisclosed = invalid)
- [ ] Deflated Sharpe / PBO computable from trial log: {{yes/no}}
- [ ] Holdout untouched: {{yes/no}}
- **Result:** {{PASS/FAIL}}

## 4. Data integrity
- [ ] Point-in-time universe, delisted names included
- [ ] As-reported fundamentals with lags (if applicable)
- **Result:** {{PASS/FAIL}}

## 5. Sample & regimes
- Trades: {{n}} → {{REJECT(<30)/WARN(30-199)/PASS(≥200)}}
- Regimes: {{bull}} {{bear}} {{high-vol}} {{low-vol}}
- Parameter plateau (neighbors also work): {{yes/no}}

## Verdict
{{VALID / FRAGILE / INVALID — with the single most important reason}}

Sources: failure-modes.md §1-3; citations S26/S27/S3/S4.
