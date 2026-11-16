# DAWN REPORT — Day Trading Skill Overnight Validation
*Autonomous deep-dive + backtest + blind LLM evaluation, completed before waking.*

**Generated:** Mon Nov 16 2026, ~07:00 PT
**Awaiting user:** Full skill package on GitHub (lowf49/evidence-first-trading), all scripts verified, results archived.

(Full historical content preserved on disk locally and in repository history. See git log for the detailed sections: Executive summary, Part 1 backtests (A1/A1b/A2/A3), Part 2 blind LLM evaluation v2, PDT/$1k constraints, integrity statement.)

## 2. The honest high-ROI answer
No setup in this project produced a proven positive edge after realistic costs. The skill's value is preventive/selection (gemma abstention: -33.3R -> +35.9R, p=0.012 via skipping losing trades). Nemotron gains nothing (p=0.45). Expectancies: A1 +0.076R@0bp / -0.071R@10bp; A1b -0.003R@0bp; battery 0/16 pre-registered candidates survive 10bp.

## ADDENDUM (2026-11-16) — after the initial report

1. **Pre-registered battery ran** (`evaluation/PRE-REGISTER.md` frozen first; `scripts/backtest_battery.py`; `evaluation/battery-results.md`). **0/16 candidates survive 10bp costs.** Honest null, on record.
2. **Free-model availability audited**: Cloudflare exposes zero models; opencode free = 12 names (most daily-limited), opencode-go = 4 (subscription/region/training-consent gates), OpenRouter free = 14 (account-wide free-models-per-day cap), Google = 0. Working at probe: opencode hy4-flash, iceman, longcat-2.5, inkling-2-small, flint-40b, beam, nemotron-3.5-lightning; OpenRouter ling-3.2, inkling-2-small. Research fleet: 8 dispatched, 7 died on limits — one of them (nemotron-3.5-lightning) had already written `research/04-cost-survival.md` before dying. Two reports ultimately landed: **02-papers.md** (web-verified here: Baltussen 2021, Zarattini & Aziz ORB, SEBI 91-93% loss rates) and **03-validation.md** (inkling-2-small: DSR/PBO/holdout/MinTRL formulas with URLs). **04-cost-survival.md** = agent-produced leads.
3. **failure-modes.md gained 8a/8b** — battery null rows + the degenerate-stop artifact (tiny stops inflate R; costs multiply via bp/risk_bp).
4. Dawn report summary: **no high-ROI/low-risk product was produced, by design. The deliverable is the honest battery, the skill, and the full evidence trail.**
