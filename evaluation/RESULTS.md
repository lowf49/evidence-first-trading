# Validation results

Three layers of validation, all reproducible from this directory.

---

## Part 1 — Deterministic historical backtest
(`python scripts/backtest_orb.py`, run 2026-11-16)

Window: 12 instruments (SPY QQQ IWM DIA AAPL NVDA TSLA MSFT AMD META AMZN GLD),
5m bars ≤60d for intraday parts, 10y daily for level stats. Data: Yahoo Finance.

### A1 — Opening Range Breakout (exact catalog rules, n=166 trades)

| Metric | Result |
|---|---|
| Win rate | **47.6%** (LONG 42.4% n=85, SHORT 53.1% n=81) |
| Expectancy @ 0bp slippage | **+0.088R** (positive) |
| @ 5bp | +0.006R (marginal) |
| @ 10bp | **−0.076R (NEGATIVE)** |
| @ 20bp | −0.240R |
| @ 50bp | −0.732R |

**Verdict: the skill's own Tier-A setup fails its own slippage sweep at 10bp —
exactly what the research predicted (ORB is cost-critical).** The skill would
flag this as FRAGILE, not tradeable without a cost advantage.

### A2 — PDH/PDL touch statistics (n=30,156 sessions, 10y, 12 symbols)

| Stat | Result | Vendor claim |
|---|---|---|
| Touch ≥1 prior-day level | **75.6%** | 89–91% (index futures) |
| Touch both | **8.8%** | ~10% (index futures) |
| Touch PDH | 45.2% | — |
| Touch PDL | 39.2% | — |

Honest divergence: single-stock/ETF touch rates run ~13pp below the vendor
index-futures numbers; the both-sweeps figure matches. The skill records its
own measured number over the vendor's.

### A3 — Last-30-min momentum (n=718 sessions)

Sign accuracy **40.9%** — below chance in this 60-day window vs Baltussen et
al.'s 53–56% (45-year study). Recorded as NOT confirmed in this sample.

---

## Part 2 — Blind LLM evaluation (gemma vs nemotron, ± skill excerpt)

### Design (anti-foreknowledge controls)

1. **Data recency** — Yahoo 5m window Oct–Nov 2026 (after any plausible
   training cutoff).
2. **Symbol masking** — `INST-01..12` with a hidden random mapping
   (`mapping.json`, never shown to models).
3. **No absolute prices, no dates** — features are % / ratios only, so
   instrument identity can't be recovered from price level.
4. **Canaries** — 3 cases carry impossible features (`or_range_pct < 0`);
   correct behavior = FLAT. Trading them = guessing without reading inputs.
5. **Baselines** — always-LONG, random (mean of 200 seeds), pure-rule.
6. **Deterministic outcomes** — computed by `blind_eval.py` in pure Python.
7. **Direct API, temperature 0** — `orchestrate.py`, ~$0.015 total, model
   replies archived as `raw_*.json`.

Dataset: **381 cases** (228 tradeable, 132 no-setup controls, 3 canaries).

### Results (60-minute direction accuracy)

| Condition | Calls | Abstain | Dir acc | 95% CI | netR @10bp | No-setup→FLAT | Canary→FLAT |
|---|---|---|---|---|---|---|---|
| BASELINE always-LONG | 228 | 0 | 45.6% | [39.3, 52.1] | −0.088 | 0% | 100% |
| BASELINE random (200-seed mean) | 153 | 75 | 50.2% | — | −0.012 | 34% | 100% |
| BASELINE pure-rule (no LLM) | 228 | 0 | 55.7% | [49.2, 62.0] | −0.441 | 100% | 100% |
| **gemma + skill** | 173 | 55 | **54.9%** | [47.5, 62.1] | **+0.075** | **73%** | **100%** |
| gemma no skill | 227 | 1 | 52.9% | [46.4, 59.3] | +0.013 | 0% | **0%** |
| nemotron + skill | 137 | 91 | 49.6% | [41.4, 57.9] | **+0.163** | 29% | **100%** |
| nemotron no skill | 194 | 34 | 49.0% | [42.0, 56.0] | +0.035 | 3% | **0%** |

Paired exact McNemar (cases both conditions called):
gemma skill-vs-noskill: 25 vs 19, **p = 0.45** · nemotron: 2 vs 6, **p = 0.29**.

### Findings

1. **No model shows a real directional edge.** Every confidence interval
   includes 50%. The blind design worked: with masked symbols, %-only
   features and post-cutoff data, there is no foreknowledge to exploit — and
   none was found.
2. **The skill's effect is behavioral, not predictive.** With the skill
   excerpt: canary compliance jumps **0% → 100%** for both models (without it
   they traded impossible inputs — direct evidence of guessing), no-setup
   abstention rises (gemma 0% → 73%), and net expectancy at 10bp improves in
   both models (+0.013→+0.075, +0.035→+0.163). Direction accuracy itself does
   not improve significantly (McNemar p = 0.45 / 0.29).
3. **Model choice matters for rule-following, not for prediction.**
   gemma-4-31b applied the no-setup rule far better than
   nemotron-3.5-lightning (73% vs 29% FLAT on controls) and abstained more
   sensibly (abstains on setups: gemma 24% of tradeables vs nemotron 40%,
   while nemotron still called 71% of no-setup cases). Direction accuracy
   differences between models are not statistically significant.
4. **The deterministic pure rule matched or beat every model on raw accuracy**
   (55.7%) — consistent with the skill's thesis: LLMs add process discipline
   (input validation, abstention, cost awareness), not predictive power. The
   rule's negative netR comes from mechanically trading every PDH/PDL-prox
   case, which models with the skill selectively avoided.

### Reproduce

```bash
python evaluation/blind_eval.py build    # rebuild cases/answers (data shifts daily)
python evaluation/blind_eval.py prompt
python evaluation/orchestrate.py run     # calls OpenRouter (key from opencode auth)
python evaluation/orchestrate.py parse
python evaluation/blind_eval.py score    # table + McNemar + score_report.json
```

---

**Bottom line:** the skill's value is loss-prevention and process — verified
by canary compliance, selective abstention, and cost-gated math — not alpha.
This matches the underlying research: no published mechanism turns an LLM (or
a retail trader) into a net-of-cost directional predictor.
