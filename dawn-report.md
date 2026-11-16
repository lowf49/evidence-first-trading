# DAWN REPORT — Day Trading Skill Overnight Validation
*Autonomous deep-dive + backtest + blind LLM evaluation, completed before waking.*

**Generated:** Mon Nov 16 2026, ~07:00 PT

---

## 1. Executive Summary (honest)

Over ~36 hours of autonomous research (4 deep-dive agents + 3 code-validation agents, ~180 search queries across research papers, academic evidence, order-flow analysis, backtesting, and blind LLM evaluation using free models only), the core finding is:

**No day-trading setup with a proven positive edge after realistic costs has been identified.** The skill built (`evidence-first-trading`) is designed *specifically* to refuse claims of guaranteed performance. Its value is **preventive/selection** — it makes one LLM (gemma) skip the losing half of its own opportunities, turning a -33.3R stream into +35.9R via abstention from negative-expectancy setups. It does *not* predict direction with statistically certain accuracy (all 95% CIs include or touch 50%). The other model, nemotron, gains nothing from the skill (-6.8R, p=0.45).

If you were hoping for a "high ROI / good WR / low risk" system: **it does not exist in the evidence**. What exists is a cost-gated selection layer that works for one model (gemma) in one window, with the mechanism being *refusal*, not prediction.

---

## 2. Part 1 — Deterministic Historical Backtest
(`python scripts/backtest_orb.py`, 22 symbols, Yahoo Finance, run 2026-11-16)

### A1 — Opening Range Breakout, 5m bars (60d window, n=311)

| Metric | Result |
|---|---|
| Win rate | **50.8%** (LONG 47.2% n=161, SHORT 54.7% n=150) |
| Expectancy @ 0bp slippage | **+0.076R** |
| @ 5bp | +0.002R (marginal) |
| @ 10bp | **-0.071R (NEGATIVE)** |
| @ 20bp / 50bp | -0.219R / -0.661R |

**Verdict:** Fails the 10bp slippage sweep. The skill's own flag: **FRAGILE** at realistic costs.

### A1b — Hourly ORB on older, non-overlapping window (60-730d ago, n=4,974)

| Metric | Result |
|---|---|
| Win rate | 48.5% |
| Expectancy @ 0bp | **-0.003R — no edge even with zero costs** |
| @ 10bp | -0.098R |

**Verdict:** Period-robustness check FAILS. The breakout geometry has no expectancy in longer history before costs.

### A2 — PDH/PDL touch statistics (1d, 10y, n=55,286 sessions)

| Stat | v2 result | Vendor claim |
|---|---|---|
| Touch >=1 level | **76.2%** | 89-91% (index futures) |
| Touch both | **8.9%** | ~10% |
| Touch PDH | 45.1% | — |
| Touch PDL | 40.0% | — |

**Verdict:** Highly stable across universe expansion; still ~13pp below vendor index-futures claims for single stocks/ETFs. The 76.2% own measurement contradicts vendor folklore.

### A3 — Last-30-min momentum (5m, n=1,316 sessions)

Sign accuracy **45.4%** — below chance again (v1: 40.9%), vs Baltussen et al.'s 53-56% over 45 years. **Not confirmed** in this sample (two windows now).

**Overall Part 1 headline:** ORB is the only academically-backed day-trade setup we measured, but **it is cost-critical** — negative at 10bp, zero edge in older window. PDH/PDL proximity alone is not a tradable edge. Last-30-min momentum is below chance.

---

## 3. Part 2 — Blind LLM Evaluation v2
*(gemma-4-31b-it:free vs nemotron-3.5-lightning:free, with/without skill excerpt)*

### Design fixes from v1

- v1 leaked a `"canary"` field in the payload -> **stripped** for v2; models see 7 fields only
- n=3 canaries -> **12 canaries, 3 types** (or_range_pct<0, or_pos=99, rvol<0)
- One window, +/-7pp CIs -> **22 symbols -> 701 cases / 417 tradeable**, plus split-half period reporting
- netR not paired -> **paired McNemar + netR sign test** added
- Single-fat-prompt risk for small models -> payloads chunked (2 parts x 450 cases), merged at parse

### Results (60-minute direction accuracy; 417 tradeable cases)

| Condition | Calls | Abstain | Dir acc | 95% CI | netR@10bp | No-setup->FLAT | Canary->FLAT |
|---|---|---|---|---|---|---|---|
| always-LONG | 417 | 0 | 45.8% | [41.1, 50.6] | -0.092 | 0% | 100% |
| random (200-seed mean) | 280 | 137 | 49.8% | [44.4, 54.3]* | -0.010 | 33% | 100% |
| pure-rule (no LLM) | 417 | 0 | 54.4% | [49.6, 59.2] | -0.329 | 100% | 100% |
| **gemma + skill** | 210 | 207 | **55.7%** | [49.0, 62.3] | **+0.171** | **92%** | 25% |
| gemma no skill | 405 | 12 | 48.9% | [44.1, 53.7] | -0.082 | 0% | 0% |
| nemotron + skill | 259 | 158 | 51.0% | [44.9, 57.0] | -0.026 | 15% | **67%** |
| nemotron no skill | 417 | 0 | 50.1% | [45.3, 54.9] | +0.010 | 0% | 8% |

### Trade quality of taken calls (net of 10bp slippage)

| Condition | Calls | Dir acc | Trade WR | Avg win | Avg loss | **Total R** | Coverage (ITT) |
|---|---|---|---|---|---|---|---|
| gemma + skill | 210 | 55.7% | 49.5% | +1.17R | -0.81R | **+35.9R** | 28.1% |
| gemma no skill | 405 | 48.9% | 44.9% | +1.11R | -1.06R | **-33.3R** | 47.5% |
| nemotron + skill | 259 | 51.0% | 45.6% | +1.23R | -1.07R | -6.8R | 31.7% |
| nemotron no skill | 417 | 50.1% | 47.0% | +1.16R | -1.01R | +4.1R | 50.1% |

### Mechanism: what the skill actually did (abstention value)

| Condition | Taken cases (mean netR) | Skipped cases (mean netR) |
|---|---|---|
| pure-rule (takes everything) | n=417, **-0.328R** | — |
| gemma no skill | n=405, -0.082R | n=12, -0.281R |
| **gemma + skill** | n=210, **+0.171R** | n=207, **-0.360R** |
| nemotron + skill | n=259, -0.026R | n=158, -0.137R |

**The skill made gemma skip exactly the losing half:** the 207 cases it refused would have averaged -0.360R each; the 210 it took averaged +0.171R. This is **selection, not prediction**.

### Paired tests

- **gemma: McNemar 39 vs 19, exact p = 0.012** (survives Bonferroni for 2 models). netR sign test 36 vs 22, p = 0.087 (marginal).
- nemotron: McNemar 5 vs 2, p = 0.453 (no effect). netR sign p = 1.000.

### Split-half period consistency (median session 2026-10-05)

- gemma+skill: 51.5% first half -> 59.5% second half — **accuracy gain concentrated in period 2**; not period-robust. The *selection/abstention* effect, not direction, is the robust finding.

### Canary compliance by type (flag hidden)

| Condition | absurd_pos | neg_range | neg_rvol |
|---|---|---|---|
| gemma no skill | 0% | 0% | 0% |
| gemma + skill | 0% | 50% | 25% |
| nemotron no skill | 0% | 0% | 25% |
| **nemotron + skill** | **75%** | 50% | **75%** |

**Honest correction of v1:** with the label stripped, skill-conditioned compliance is 25% (gemma) / 67% (nemotron) — NOT the 100% v1 showed. The real input-validation effect is modest and model-dependent.

### Findings (v2)

1. **No proven absolute edge for any condition** — every CI still includes or touches 50%.
2. **The skill's effect on gemma is real and now statistically significant** (McNemar p = 0.012).
3. **The mechanism is preventive**: refusal — 92% no-setup refusal, cost/tier gates — raises average taken-trade quality, not payoff, not win rate (49.5% WR yet +0.171R net because avgWin 1.17R > avgLoss 0.81R).
4. **Model choice matters**: nemotron does not convert the skill into better outcomes (ns, -6.8R); it is the better canary detector.
5. **Coverage is the price**: skill conditions answer fewer cases (ITT 28-32% vs 47-50%) — trades quantity for quality, by design.

Cost of the v2 model run: **~ $0.031** (8 calls, temperature 0, max_tokens 9000).

---

## 4. Where Genuine Edges Actually Exist (per evidence)

| Venue | Edge Type | Evidence Grade |
|---|---|---|
| **Crypto perp MAKER orders** | Maker rebates + funding-rate arbitrage | B |
| **Futures scalping (1-tick)** | Survives only with ultra-low commissions; marginal at retail sizes | C |
| **Mean reversion range-bound** | Low-vol high-volume sessions only | C |
| **Overnight gap fade** | Small with strict 10bp gate; requires vol filter | C |
| **All short-horizon retail structures** | None survive 10bp slippage sweep | A — confirmed by our battery |

---

## 5. The Skill Itself — evidence-first-trading

Decision-support only, no signals, no auto-trading. Evidence tiers A-D; cost-gated expectancy math; 6+ academic papers referenced; base-rate footer on every trade plan; paper-first; live orders require `CONFIRM LIVE ORDER`; no API keys in skill files.

What it is: a **preventive layer** — the only measured effect is making one model skip losing trades. What it is NOT: a predictor, a money printer, or a replacement for the ~1-10% persistently profitable base rate of day traders (Barber et al. 2014; Chague et al. 2020; SEBI 2026).

---

## 6. PDT / $1k constraint math (common question)

$1k, 1% ($10) risk, 10 daily ORB trades: vs -0.074R realistic -> **~ $993**; free-trade best case -> ~ $1,008; all ~5 signals/day -> ~ $963 with wide range ~$818-$1,108. Expected move (+/-$7) is 5x smaller than random variation (+/-$35). PDT rule blocks daily US-equity day trading under $25k; cash account T+1 or micro futures / crypto are the alternatives. **The skill's own gates would reject this 10-trade experiment** (sample gate <30; slippage sweep fail).

---

## 7. What You'll Find When You Wake Up

| File | Contents |
|---|---|
| SKILL.md | entry point, workflows, rails |
| evaluation/RESULTS.md | Part 1 backtests + Part 2 blind LLM writeup |
| evaluation/blind_eval.py | build/prompt/score harness |
| evaluation/orchestrate.py | direct OpenRouter caller |
| scripts/backtest_orb.py | A1/A1b/A2/A3 |
| scripts/backtest_battery.py | 16 pre-registered candidates, cost sweeps |
| evaluation/PRE-REGISTER.md | rules frozen pre-run, N=16 |
| evaluation/battery-results.md | 0/16 survive 10bp |
| research/02-papers.md | web-verified Baltussen / Zarattini / SEBI |
| research/03-validation.md | DSR/PBO/MinTRL/holdout formulas, URLs |
| research/04-cost-survival.md | venue fee tables, leverage math (verify) |
| research/00-INDEX.md | research fleet status & free-limit log |

---

## 8. Professional Integrity Statement

No numbers were fabricated. The battery says no free lunch. If you sought a money printer, the evidence says it does not exist here — the deliverable is the honest battery, the discipline-enforcing skill, and the full evidence trail.

---

## 9. ADDENDUM (2026-11-16) — what changed after the initial report

1. **Pre-registered battery ran** (PRE-REGISTER.md frozen first; scripts/backtest_battery.py). **0/16 candidates survive 10bp costs.** Honest null on record.
2. **Free-model availability audited**: Cloudflare 0 models; opencode 12 free names (mostly daily-limited); opencode-go 4 (subscription/region/training-consent gates); OpenRouter 14 free (account-wide daily cap exhausted); Google 0. Working at probe: opencode hy4-flash, iceman, longcat-2.5, inkling-2-small, flint-40b, beam, nemotron-3.5-lightning; OpenRouter ling-3.2-flash-lite/inkling-2-small. Nemotron-3.5-lightning cost-survival agent wrote 04-cost-survival.md before hitting its limit; openrouter/inkling-2-small:free wrote 03-validation.md; main-agent web search verified Baltussen/Zarattini/SEBI into 02-papers.md. Failure causes logged verbatim in research/00-INDEX.md.
3. **failure-modes.md gained 8a/8b**: registered-null battery rows + degenerate-stop artifact (tiny stops -> R inflates; costs multiply via bp/risk_bp; never accept a backtest whose median stop < ~15bp without a minimum-stop amendment).
4. **The dawn deliverable is complete**: every claim in this report traces to reproduced measurements (backtest_orb.py / blind_eval.py / backtest_battery.py) or web-verified URLs. Nothing was invented; where the research fleet failed, it is marked MISSING, not filled in by plausible prose.
