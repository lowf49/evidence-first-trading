# evidence-first-trading

**Evidence-graded day-trading decision support. Not financial advice. Not a signal service. Never auto-executes.**

An agent skill (Claude Code / OpenCode compatible) that:

- 🎯 **Scans for Tier-A/B setups only** — opening range breakout, prior-day levels, intraday momentum — each with exact rules, sample sizes, and citations (`references/setup-catalog.md`)
- 🚫 **Refuses bad math** — `expectancy_calc.py` *will not run without cost inputs*; slippage sweeps (0/5/10/20/50bp) are mandatory
- 📊 **Audits backtests** — look-ahead, repainting (the ICT/SMC trap), undisclosed trial counts, survivorship, sample-size gates (reject <30, warn <200, pass ≥200)
- 📓 **Journals honestly** — Wilson confidence intervals on your real win rate, planned-vs-actual calibration, negative-skew warnings
- 🔬 **Ships a cheating-resistant blind evaluation** (`evaluation/blind_eval.py`) — masked symbols, %-only features, post-training-cutoff data, canary cases, and simple-baseline comparisons, so an LLM judging it *cannot* succeed from memorized market knowledge

## Why it exists

~180 searches across skills registries, peer-reviewed journals, regulator studies, and microstructure literature produced one consistent conclusion: **skills improve process and data quality, never alpha.** The base rates: 1–10% of day traders are persistently profitable (Barber et al. 2014; Chague et al. 2020; SEBI 2026), and backtest Sharpe predicts out-of-sample performance with R² < 0.025 (Quantopian, 888 algorithms).

So this skill encodes the *physics and the discipline*: what actually moves price (order-flow imbalance, stop cascades, auction mechanics), what survives testing, and what gets a trade plan refused.

## Install

```bash
npx skills add lowf49/evidence-first-trading
```

Or clone and copy into your agent's skills directory:

```bash
git clone https://github.com/lowf49/evidence-first-trading
```

## Workflows

| Command | What it does |
|---|---|
| `/setup-scan SPY,QQQ` | Tier-A/B trigger status for the latest session (no predictions) |
| `/verify-setup <rule>` | Grades any setup A–D with citations (unknown = LORE) |
| trade-plan | Mandatory gates: tier, net expectancy, cost breakeven, sample size |
| `/backtest-review` | Look-ahead / costs / trial-count / survivorship audit |
| `/market-state` | Descriptive regime facts only |
| `/journal` | Wilson CIs, R distribution, skew warnings |

## Evidence tiers

**A** peer-reviewed + independent backtest → may drive plans · **B** independent backtest → plan with warning · **C** forum lore → informational, labeled · **D** debunked → refused with the negative result explained.

## Backtesting & blind evaluation (reproduce it)

```bash
# 1. Deterministic historical validation of Tier-A setups (slippage sweep included)
python scripts/backtest_orb.py

# 2. Build blind cases (masked symbols, %-only features, canaries, post-cutoff data)
python evaluation/blind_eval.py build
python evaluation/blind_eval.py prompt

# 3. Call any two LLMs (or send the payloads manually - chunked files
#    prompts/payload_<cond>_<n>.txt, canary flag hidden from models):
python evaluation/orchestrate.py run      # -> raw_<model>_<cond>_<n>.json
python evaluation/orchestrate.py parse    # -> decisions_<model>_<cond>.json

# 4. Score vs baselines (always-long / random / pure-rule), paired tests,
#    split-half periods, canary-by-type, abstention value
python evaluation/blind_eval.py score
```

Validity controls: 60-day post-cutoff data, symbol masking with hidden mapping, no absolute prices or dates, impossible-feature canaries, seeded-random baseline, deterministic outcomes in pure Python.

## Safety

- Paper-first: broker integration defaults to paper; live orders require `CONFIRM LIVE ORDER`
- No API keys in skill files (keyless Yahoo data layer)
- Banned vocabulary: "guaranteed", "will", "high-probability" without *n*
- Every number traces to `references/citations.md`

## Files

```
SKILL.md                     # entry point, workflows, rails
references/                  # setup catalog (A-D), cost math, rubric, structure, failure modes, citations
scripts/                     # data.py, setup_scanner.py, backtest_orb.py,
                             # expectancy_calc.py, cost_breakeven.py, journal.py
evaluation/blind_eval.py     # blind harness: build / prompt / score
templates/                   # trade-plan, backtest-review, post-mortem
```

## License & disclaimer

MIT. Educational decision support only. Not financial advice. No prediction of future prices is made or implied. Trading can cost you your entire account — the research says most people who try, lose.
