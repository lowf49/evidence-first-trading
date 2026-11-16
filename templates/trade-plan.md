# Trade plan — {{symbol}} {{direction}} {{date}}

**Setup / tier:** {{setup}} — Tier {{A/B}} (source: {{citation}})
**Historical evidence:** {{hit rate / frequency}} (n={{n}}, {{date range}}, {{source}})

## Trigger (exact)
- Entry trigger: {{rules as fired}}
- Entry: {{price}}  · Stop: {{price}}  · Target: {{price}}
- R definition: {{risk per share/unit}} = {{risk}} ({{risk_bp}} bp)

## Gates
- [ ] Tier is A or B (C = lore, D = refused)
- [ ] Net expectancy computed WITH costs → {{+x.xxx}} R/trade at {{slippage}} bp
- [ ] Slippage sweep: 0bp {{+x}} · 5bp {{+x}} · 10bp {{+x}} · 20bp {{+x}} · 50bp {{+x}}
- [ ] Sample gate: n={{n}} → {{REJECT/WARN/PASS}} (≥30 floor, ≥200 confidence)
- [ ] Regimes covered: {{bull/bear/high-vol/low-vol}}
- [ ] Position size ≤ {{x}}% of account; risk ≤ {{x}}R

## Refusal conditions (stop if any true)
- Cost inputs missing · n<30 · setup not in catalog · parameter chosen by max-backtest-Sharpe ·
  repainting/look-ahead found in the backtest · I cannot cite the claim

---
**Base rate footer:** ~1–10% of day traders are persistently profitable; 87–97% of retail
day traders lose net of costs (Barber et al. 2014; Chague et al. 2020; SEBI 2026).
This plan is decision support, not a prediction.
