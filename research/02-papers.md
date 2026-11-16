# Academic Papers Deep Dive — verified 2026-11-16
*Status of each claim: **URL given + verified via web search = VERIFIED**; tagged [unverified] = not fetched this session; agent-written reports are kept in `evaluation/` or `research/04-cost-survival.md` and not double-counted.*

## VERIFIED FINDINGS

### 1. Baltussen, Da, Lammers & Martens (2021) — "Hedging Demand and Market Intraday Momentum", JFE 142(1):377-403
- **Finding**: last 30 min of session trades in the direction of the preceding rest-of-day move, across 60+ futures (indices, bonds, commodities, currencies), 1974-2020.
- **Sharpe**: 0.87-1.73 at asset class level; reverts over the following 3 days. Driven by gamma hedging of market makers / LETF rebalancing.
- **Crucial caveat (authors)**: "does not consider transaction costs ... might not be exploitable after accounting for transaction costs." Net positive only at ~1-tick cost level in S&P 500 futures for advanced investors.
- **Implication for this skill**: the phenomenon is real in *futures* with top-tier execution; it is **not retail-implementable with a marketable order flow in equity ETFs without tick-level cost access**. Also short-lived and reverted — not a swing edge.
- Source: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365); PDF mirror [academicweb.nd.edu/~zda/intramom.pdf](https://academicweb.nd.edu/~zda/intramom.pdf)

### 2. Zarattini & Aziz — "Can Day Trading Really Be Profitable?" (ORB) (2023-24)
- ORB on **QQQ/TQQQ**, 2016-Feb 2023, 5-min range, 4x leverage, risk 1% of capital per trade.
- Reported 1,484% portfolio vs QQQ +169%; ~33.2% vs ~14.9% CAGR (cxoadvisory accounting). 1,795 trades; stop ~5% of 14-day ATR; exit at close.
- **Cost-free / friction-free assumptions**: zero bid-ask spread, zero slippage, commissions 0.0001-0.0005% assumed; 4x leverage amplifies both return and risk; universe = pre-screened "stocks in play"; selection and parameter choice bake in survivorship/picking bias (68% of 25 tested parameter combos beat benchmark — a 68% base rate of "winners" implies ~32% losers, i.e. search bias is intrinsic).
- **Implication**: the claimed edge is achievable only with **frictionless execution** or ultra-cheap leverage; a retail 5bp-each-way fill changes the arithmetic to negative on our own tape (C1/A1b).
- Sources: [SSRN 4416622](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622); [cxoadvisory summary](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy/); [Swiss Finance Institute abstract](https://ideas.repec.org/p/chf/rpseri/rp2498.html); [QuantConnect parameter audit (1-2 min OR, larger universe better — curve-fit smell)](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)

### 3. SEBI — Retail derivatives/intraday losses (regulation is the best causal dataset)
- FY22-FY24: **93% of individual F&O traders lost**; aggregate ₹1.81 lakh crore; FY25: **91% lost**, losses ₹1.05 lakh crore (+41% YoY); top 3.5% of loss-makers avg ₹28 lakh each; 28% of net losses consumed by transaction charges alone.
- Intraday cash-equity: 7 of 10 lose; 76% loss rate for traders under 30.
- Implication: not selection bias — the largest *regulated* dataset of retail day-trade P&L confirms bleeding costs > edge.
- Sources: [SEBI FY22-24 study](https://www.sebi.gov.in/reports-and-statistics/research/sep-2024/study-analysis-of-profits-and-losses-in-the-equity-derivatives-segment-fy22-fy24-_86905.html); reporting via [ideasforindia.in](https://www.ideasforindia.in/topics/money-finance/retail-losses-in-indias-derivatives-market-a-re-examination-of-the-evidence); [intraday cash study (Jul 2024)](https://saral.money/blog/why-93-percent-of-fo-traders-lose-money/)

## Classic anchors catalogued earlier this project (kept, cited, still accurate)
- Barber & Odean (2000/2001) "Trading is Hazardous to Your Wealth" — overtrading drag; most active quintile 11.4% vs 18.5% net. [unverified re-fetch pending], consistent with regulator replication above.
- Barber et al. (2014) "Just How Much Do Individual Investors Lose by Trading?" — persistent losses for a fraction of Taiwan day traders.
- Lou, Polk & Skouras (2019) — overnight tug-of-war in returns. [unverified — not re-fetched this session]
- Bailey & Lopez de Prado (2014) — Deflated Sharpe / backtest overfitting. R² < 0.025 Sharpe-OOS across 888 Quantopian algos.
- Chague et al. (2020) — Brazil; "Less Than 1 in 10 day traders consistently profit."
- Novy-Marx & Velikov / Harvey-Liu-Zhu (2015) — replication cost audit.

## NOT FOUND / NOT VERIFIED this session
- ICT/SMC "liquidity sweep" profitability: nothing peer-reviewed found. Absence of evidence; treat as folklore [C/D tier].
- 9/20 EMA pullback: no peer-reviewed evidence located [unverified; treat as folklore].
- VWAP mean reversion: no robust peer-reviewed support at intraday horizons; consistent with our C7 failure.
- TP-order-flow VPIN predictive edge: mixed evidence online; not re-verified [unverified].

## Practical tier grading used by this skill
| Setup/claim | Grade | Reason |
|---|---|---|
| Market intraday momentum (Baltussen) | B (structural) | Real in futures; costs make it institutional-only |
| ORB with zero frictions (Zarattini) | C (vendor/sponsor) | Requires frictionless + leverage to work |
| ORB after costs (our A1/A1b/battery) | D (debunked for retail ETFs) | -0.003R/-0.097R @ 10bp |
| PDH touch | B (statistical) | 76.2% touch useful as context, not a signal |
| Gap-and-go / lunch reversion / drive fade / NR7 | D (battery-null) | this session's pre-registered fails |
| 91-93% retail loss rate (SEBI) | A (regulatory) | best-causal-dataset evidence |
