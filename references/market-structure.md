# Market structure — what actually moves price (Tier-1 evidence)

This is the skill's physics layer. Signals sit on top of this.

1. **Order-flow imbalance (OFI) drives short-horizon price, linearly, with slope = 1/depth** — Cont, Kukanov & Stoikov 2014 [S1]. Practical: market orders and cancellations are all priced through OFI; identical flow moves price differently depending on book state.
2. **Execution costs are regime-dependent** — price-impact coefficients ~5× higher 09:30–10:00 than later; depth at the open ≈ half the daily average [S1]. The open has the most volatility AND the worst execution economics (U-shape [S6]).
3. **Stop cascades are real and documented** — Osler 2005 on a complete order book: stops = 43–45% of orders; price accelerates through stop clusters (just beyond round numbers/swing levels), triggered in waves, larger & longer-lasting than take-profit clusters [S5]. This is the validated core of "liquidity grabs".
4. **Derivatives lead cash** — futures lead the cash index up to ~45 min historically, still leading around macro releases; options lead futures [S2].
5. **Auctions anchor the open** — NYSE opening auction ≈ 44M shares/day with imbalance messages every second from 08:00 ET (free) [S7]; morning auction contributes ~11.8pp more price discovery than afternoon.
6. **Time-of-day premia** — momentum accrues ~100% overnight (0.98%/mo, t=3.84); size/value intraday (Lou–Polk–Skouras 2019) [S2]; pre-FOMC 24h drift (Lucca–Moench 2015) [S2].
7. **Volatility clusters** (GARCH) and intraday vol/volume follow a U [S6][S2].
8. **Dealer gamma is a weather map, not a compass** — mechanism settled (short gamma amplifies, long damps), but average MM net gamma ≈ 0.04–0.17% of futures volume and dealer inventory sign is modeled, not observed; vendors themselves say "GEX does not predict direction" [S29].
9. **VPIN/flow toxicity** — legitimate description of imbalance in volume time, but no incremental vol prediction after controlling for intensity; failed as a real-time flash-crash warning (Andersen & Bondarenko 2014) [S29].
10. **Non-informational flow matters** — retail attention buying underperforms (−4.7%/20d) [S9]; forced buying (squeezes, stop cascades, portfolio-insurance) explains fat tails without news [S5][S2].

## Folklore vs physics
| Practitioner concept | Physics underneath | Status |
|---|---|---|
| Absorption / exhaustion / delta | coarse OFI readings | mechanically real, predictive claim untested |
| Volume profile POC/value area | depth clustering at reference levels | placement real; "attractor" edge untested |
| DOM/ladder direction reading | 1/depth impacts | no retail evidence; "spot the algo" edge decayed |
| Round-number magnet | stop clusters + clustering stats | weak magnet, strong *location* effect [S19][S5] |
