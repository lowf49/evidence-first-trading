# Validation results

Three layers of validation, all reproducible from this directory.
**Current results are v2** (v1 artifacts archived in `evaluation/v1/` — see
"design fixes" below).

---

## Part 1 — Deterministic historical backtest
(`python scripts/backtest_orb.py`, run 2026-11-16, 22 symbols)

Universe: SPY QQQ IWM DIA AAPL NVDA TSLA MSFT AMD META AMZN GLD NFLX JPM XOM
UNH COST DIS BA INTC MU TLT. Data: Yahoo Finance.

### A1 — Opening Range Breakout, 5m bars (exact catalog rules, 60d window, n=311)

| Metric | Result |
|---|---|
| Win rate | **50.8%** (LONG 47.2% n=161, SHORT 54.7% n=150) |
| Expectancy @ 0bp slippage | **+0.076R** |
| @ 5bp | +0.002R (marginal) |
| @ 10bp | **−0.071R (NEGATIVE)** |
| @ 20bp / 50bp | −0.219R / −0.661R |

**Fails the 10bp slippage sweep** — the skill would flag FRAGILE.

### A1b — Hourly ORB on an OLDER, non-overlapping window (60–730 days ago, n=4,974)

| Metric | Result |
|---|---|
| Win rate | 48.5% |
| Expectancy @ 0bp | **−0.003R — no edge even with zero costs** |
| @ 10bp | −0.098R |

**Period-robustness check FAILS the setup**: in the longer historical window
the same breakout geometry has no expectancy at all before costs. This is the
strongest negative result in the skill's own testing and is recorded as such.

### A2 — PDH/PDL touch statistics (1d, 10y, n=55,286 sessions)

| Stat | v2 result | v1 (12 symbols) | Vendor claim |
|---|---|---|---|
| Touch ≥1 level | **76.2%** | 75.6% | 89–91% (index futures) |
| Touch both | **8.9%** | 8.8% | ~10% |
| Touch PDH | 45.1% | 45.2% | — |
| Touch PDL | 40.0% | 39.2% | — |

Highly stable across universe expansion; still ~13pp below vendor index-futures
claims for single stocks/ETFs.

### A3 — Last-30-min momentum (5m, n=1,316 sessions)

Sign accuracy **45.4%** — below chance again (v1: 40.9%), vs Baltussen et al.'s
53–56% over 45 years. **Not confirmed in this sample** (two windows now).

---

## Part 2 — Blind LLM evaluation v2 (gemma vs nemotron, ± skill excerpt)

### Design fixes from v1 (the caveats you flagged)

| Caveat | Fix in v2 |
|---|---|
| v1 leaked a `"canary"` field in the payload | **Flag stripped** — models see 7 fields only; canaries must be detected from impossible values |
| n=3 canaries | **12 canaries, 3 types** (`or_range_pct<0`, `or_pos=99`, `rvol<0`) |
| One window, ±7pp CIs | **22 symbols → 701 cases / 417 tradeable**, plus split-half period reporting |
| netR not paired | **Paired netR sign test** added alongside McNemar |
| Single-fat-prompt risk for small models | Payloads chunked (2 parts × 450 cases), merged at parse |

Remaining limitations (cannot be fixed here): single 60d window (Yahoo caps 5m
data at 60 days; older-period coverage comes from Part 1 A1b instead), models
received a condensed rules excerpt rather than the full skill workflow, and
netR uses a mirror approximation when a model's direction differs from the
rule's. v1 (n=381) is archived in `evaluation/v1/` for comparison.

### Results (60-minute direction accuracy; 417 tradeable cases)

| Condition | Calls | Abstain | Dir acc | 95% CI | netR@10bp | No-setup→FLAT | Canary→FLAT |
|---|---|---|---|---|---|---|---|
| always-LONG | 417 | 0 | 45.8% | [41.1, 50.6] | −0.092 | 0% | 100% |
| random (200-seed mean) | 280 | 137 | 49.8% | [44.4, 54.3]* | −0.010 | 33% | 100% |
| pure-rule (no LLM) | 417 | 0 | 54.4% | [49.6, 59.2] | −0.329 | 100% | 100% |
| **gemma + skill** | 210 | 207 | **55.7%** | [49.0, 62.3] | **+0.171** | **92%** | 25% |
| gemma no skill | 405 | 12 | 48.9% | [44.1, 53.7] | −0.082 | 0% | 0% |
| nemotron + skill | 259 | 158 | 51.0% | [44.9, 57.0] | −0.026 | 15% | **67%** |
| nemotron no skill | 417 | 0 | 50.1% | [45.3, 54.9] | +0.010 | 0% | 8% |

\* random row CI = 95% band across 200 seeds, not a binomial CI.

### Trade quality of taken calls (net of 10bp slippage)

| Condition | Calls | Dir acc | Trade WR | Avg win | Avg loss | **Total R** | Coverage (ITT) |
|---|---|---|---|---|---|---|---|
| gemma + skill | 210 | 55.7% | 49.5% | +1.17R | −0.81R | **+35.9R** | 28.1% |
| gemma no skill | 405 | 48.9% | 44.9% | +1.11R | −1.06R | **−33.3R** | 47.5% |
| nemotron + skill | 259 | 51.0% | 45.6% | +1.23R | −1.07R | −6.8R | 31.7% |
| nemotron no skill | 417 | 50.1% | 47.0% | +1.16R | −1.01R | +4.1R | 50.1% |

### Mechanism: what the skill actually did (abstention value)

| Condition | Taken cases (mean netR) | Skipped cases (mean netR) |
|---|---|---|
| pure-rule (takes everything) | n=417, **−0.328R** | — |
| gemma no skill | n=405, −0.082R | n=12, −0.281R |
| **gemma + skill** | n=210, **+0.171R** | n=207, **−0.360R** |
| nemotron + skill | n=259, −0.026R | n=158, −0.137R |

**The skill made gemma skip exactly the losing half**: the 207 cases it
refused would have averaged −0.360R each; the 210 it took averaged +0.171R.
This is selection, not prediction — the skill did not change any single
trade's payoff, it changed *which* trades were taken.

### Paired tests (both conditions called the same case)

- **gemma: McNemar 39 vs 19, exact p = 0.012** (significant; survives
  Bonferroni for 2 models). netR sign test 36 vs 22, p = 0.087 (marginal).
- nemotron: McNemar 5 vs 2, p = 0.453 (no effect). netR sign p = 1.000.

### Split-half period consistency (median session 2026-10-05)

gemma+skill: 51.5% first half → 59.5% second half — **its accuracy gain is
concentrated in period 2**, so the absolute-direction claim is not
period-robust. Pure-rule (53.5/55.4) and the no-skill models (~49–51% both
halves) were stable. The *selection/abstention* effect, not direction, is the
robust finding.

### Canary compliance by type (flag hidden)

| Condition | absurd_pos | neg_range | neg_rvol |
|---|---|---|---|
| gemma no skill | 0% | 0% | 0% |
| gemma + skill | 0% | 50% | 25% |
| nemotron no skill | 0% | 0% | 25% |
| **nemotron + skill** | **75%** | 50% | **75%** |

**Honest correction of v1**: with the label stripped, skill-conditioned
compliance is 25% (gemma) / 67% (nemotron) — *not* the 100% v1 showed.
v1's perfect score was largely the leaked `"canary"` field being obeyed. The
real input-validation effect exists but is modest and model-dependent
(nemotron, despite weaker rule-following on setups, was the better canary
detector).

### Findings

1. **No proven absolute edge for any condition** — every CI still includes or
   touches 50%. Nobody can claim "the model predicts direction" from this.
2. **The skill's effect on gemma is real and now statistically significant**
   (paired p = 0.012): +48.9% → +55.7% on shared cases, and economically
   large (−33.3R → +35.9R over the window) via abstention from the
   negative-expectancy half of setups.
3. **The mechanism is preventive**: refusal ("don't take this trade"),
   92% no-setup refusal, cost/tier gates — which raises the *average quality
   of taken trades*, not the payoff of any trade and not the win rate
   (gemma+skill's trade win rate was 49.5% — below a coin flip — yet
   expectancy positive because avgWin 1.17R > avgLoss 0.81R).
4. **Model choice matters**: nemotron does not convert the skill into better
   outcomes (ns, −6.8R) though it is the better canary detector. A weaker
   model can follow safety micro-rules yet fail to apply selection logic.
5. **Coverage is the price**: skill conditions answer fewer cases correctly
   in absolute terms (ITT 28–32% vs 47–50%) — the skill trades quantity for
   quality. That is the intended design, but it means it cannot manufacture
   accuracy on setups it declines to call.

### Reproduce

```bash
python scripts/backtest_orb.py          # Part 1 (A1/A1b/A2/A3)
python evaluation/blind_eval.py build   # rebuild cases/answers (data shifts daily)
python evaluation/blind_eval.py prompt  # chunked payloads, canary flag hidden
python evaluation/orchestrate.py run    # calls OpenRouter (key from opencode auth)
python evaluation/orchestrate.py parse  # merge parts -> decisions_<model>_<cond>.json
python evaluation/blind_eval.py score   # table + splits + paired tests + score_report.json
```

Cost of the v2 model run: **≈ $0.031** (8 calls, temperature 0, max_tokens
9000). v1 cost ≈ $0.015.

---

**Bottom line:** the skill is a loss-prevention and selection layer — it made
one model skip the losing half of its own opportunities and turned a −33R
stream into a +36R stream *in simulation*, while producing zero evidence of
predictive ability and only modest evidence of input validation. No published
mechanism turns an LLM (or a retail trader) into a net-of-cost directional
predictor; the value is in what it refuses to do.
