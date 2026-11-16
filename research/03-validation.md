# Quant Strategy Validation Methodology — How Professionals Pre-Register and Test a Strategy

**Date:** 2026-11-16 · **Scope:** methodology research for systematic trading strategy validation. Every claim carries a source URL or an explicit [unverified] tag. Formulas are reproduced from fetched sources; where sources disagree the discrepancy is flagged rather than hidden.
*(AGENT-PRODUCED by openrouter/thinkingmachines/inkling-2-small:free; local file research/03-validation.md is authoritative; this pushed copy mirrors it.)*

## 1. Pre-registration & three windows
- Development (~50-55%): rules free to examine. Validation (~25%): run ONCE, frozen candidate. Sealed holdout (~20%): opened once, never tuned on. (TradeTech Analytics; gsdaq; tradeagentlab)
- Holdout enforced in code ("HOLDOUT ALREADY CONSUMED"); frozen rules hashed by git commit; every accidental peek disclosed.
- Synthetic zero-edge best-of-many trials hit t=2.07 (~5% false positive). After 1000 zero-skill trials, expected max Sharpe ~= 3.26.

## 2. Walk-forward analysis
- Rolling (sliding) vs anchored (expanding) — run BOTH; disagreement is itself a finding.
- OOS = 10-25% of each run; ratio 3:1 to 9:1; >=5-6 non-overlapping folds; folds are NOT independent (training overlaps).
- Size windows in TRADES not months; embargo between train and test; random shuffles invalid (leakage).
- WFE = annualized OOS / annualized IS. Pardo bar ~50% (folklore, not validated); >0.8 robust; WFE>1 usually one lucky window. TradeStation fails WFE < 50%.

## 3. Purged k-fold + embargo (Lopez de Prado, AFML ch.7)
- Purge if label intervals overlap: p_i <= e_j and p_j <= e_i.
- Embargo ~1-2% of samples AFTER each test fold (forward only). CPCV: all C(N,k) combos; phi(N,k) = (k/N)*C(N,k) complete paths; N=6,k=2 -> 15 splits, 5 paths. skfolio defaults purged_size=0/embargo_size=0 — you must set them.

## 4. Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)
SR0 ~= sqrt(V[SR]) * [(1-gamma)*Phi^-1(1-1/N) + gamma*Phi^-1(1-1/(N*e))], gamma~=0.5772
SE(SR) = sqrt((1 - g3*SR + ((g4-1)/4)*SR^2)/(T-1))   — g4 PEARSON kurtosis (Gaussian=3)
DSR = Phi((SR_hat - SR0)/SE(SR))
- Per-period units only; annualize only for display.
- scipy.stats.kurtosis returns EXCESS (Gaussian=0) — add 3.
- After 1000 zero-skill trials, E[max SR] ~= 3.26. DSR > 0.95 required at 5%. N counts ALL trials incl. discarded (N=1 -> plain PSR).
- Worked example: 60 monthly returns, ann. SR 1.5, skew -1, kurt 6, N=100 -> DSR ~= 0.62 FAIL.

## 5. PBO via CSCV
- T rows x N configs; S even; C(S,S/2) splits; pick IS-best, rank OOS; omega = r/(N+1); lambda = ln(omega/(1-omega)); PBO = P(lambda <= 0).
- S=4->6, S=6->20, S=8->70, S=16->12,870. PBO<0.2 minimum, <0.1 ideal; rank the procedure not one backtest.

## 6. White's Reality Check / Hansen's SPA
- f_k,t = L_bench - L_k; T_RC = max_k sqrt(n)*f_bar_k; T_SPA = max_k sqrt(n)*f_bar_k/omega_k (studentized, drops poor models — strictly more powerful).
- Stationary bootstrap (Politis-Romano), block ~ T^(1/3); >=999 reps; bootstrap ROWS jointly across models.

## 7. Minimum Track Record Length
MinTRL = 1 + (1 - g3*SR + ((g4-1)/4)*SR^2) * (Z_(1-alpha)/(SR - SR*))^2
- SR=2 vs 1: 2.73y daily. SR=1 vs 0: ~685 daily obs (~2.7y). Hedge-fund skew/kurt: ~60 months.
- SR <= SR* -> NO finite track record suffices. Per-trade Sharpe: T = trade count.

## 8. Kelly criterion
f* = (bp - q)/b ; g(f) = p ln(1+fb) - q ln(1-f) ; ruin: P = x^(2/c - 1) (c = fraction of Kelly)
- Full Kelly: ~50% chance of halving. Half Kelly: ~12.5%; keeps ~3/4 growth at ~1/4 variance. **2x Kelly -> zero growth.**
- Win-rate sampling error at 100 trades: ~+/-5pts (95% CI 45-65%) — a 55% edge is often indistinguishable from none.

## 9. Vol targeting vs fixed fractional
w_t = min(sigma_target/sigma_hat_t, cap). Exploits vol clustering; SPY 1999-2025 example: DD -49.2% vs -56.8%, return/vol 0.58 vs 0.49. VT is risk shaping, NOT alpha; crisis lag irreducible; daily rebalancing cost can flip results; leverage cap recommended.

## 10. Risk metrics at n<500
1. Expectancy (after costs) — primary number. 2. Max DD/Calmar (window-bound, not scalable). 3. Profit factor + one-trade test (delete biggest win; if PF<1.2 -> anecdote). 4. Tail ratio (blind beyond P95). 5. WR x payoff only jointly. Sharpe >= 1.0 healthy needs >=200 trades. PF unbounded above, skewed high in small samples — always bootstrap CI.

## 11. Multiple-testing workflow
- Log EVERY trial (incl. failures). Choose ONE correction in advance: Bonferroni/Holm (single final selection; ignores dependence), BH (FDR), StepM/SPA/StepM bootstrap (finance default; handles dependence; Chordia-Goyal-Saretto endorse adaptive FPD-correction only).
- Raw alpha 0.05 over 100 tests -> ~99% chance of >=1 false positive (1-0.95^100). Harvey-Liu: 200 tests -> Bonferroni bar t>=3.66; t=2.92 fails.
- Never "test 20 pick top 5 retest". Report N, dispersion, corrected hurdle.

## 12. Holdout & paper trading
- Open holdout EXACTLY once per strategy; a checked-twice holdout is training data; OOS >> IS Sharpe implies peek (2.4 -> 1.7 plausible, 2.4 -> 2.6 contaminated).
- Paper trading tests OPERATIONS (fills, platform, timing), NOT statistics. Real fills worse than paper. Need >=30-50 trades (target 50-100); WR CI at 20 trades spans 28-72%.
- ~15-20% degradation vs backtest is normal. Live capital outweighs any backtest.

## 13. Backtest bug checklist
Look-ahead (same-bar fill; HTF resample; full-sample stats), repainting, survivorship (delisted names), fill assumptions (stop-first same-bar), timezone/session mismatch, dividend double-count, back-adjusted rolls, centered smoothing windows, overlapping ML labels (-> purged CV). Meta-check: add fake future data; nothing before it may change.

## 14. 12-step pre-registration checklist
Hypothesis -> universe+data -> signal spec -> costs (1x/2x/3x stress, survive 2x) -> sizing (fractional Kelly/vol target) -> windows declared (dev/validation/holdout) -> metrics & pass bar (DSR>=0.95, PBO<=0.2, PF>1.2) -> trial registry (N declared) -> freeze & hash -> one-shot holdout -> paper phase (>=30-50 trades) -> post-mortem kill criteria.

## Top 5 actionable findings
1. Freeze before you see; open the holdout once (hash enforced).
2. Deflate for the search actually done (DSR >= 0.95; PBO <= 0.2; ~3.26 expected max Sharpe after 1000 zero-skill trials).
3. Size in TRADES not time; ~685 daily obs needed for SR=1 vs 0 at 95%.
4. <= Half Kelly + vol targeting; 2x Kelly = zero growth; full Kelly halves capital half the time.
5. Audit the backtest (next-bar fills, delisted names, stop-first rule, dividend basis, 1-bar-lag rerun) before trusting any number.
