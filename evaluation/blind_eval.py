"""Blind, cheating-resistant evaluation harness.

Design (this is what stops models from "guessing off foreknown knowledge"):
  1. DATA RECENCY  - Yahoo 5m covers <=60d. Window = Oct-Nov 2026, AFTER any
                     plausible training cutoff of gemma-4 / nemotron-3.5.
  2. SYMBOL MASK   - symbols replaced by INST-xx with a per-run random mapping
                     (evaluation/mapping.json is never shown to models).
  3. NO ABSOLUTE PRICES - features are % / ratios only, so instrument identity
                     can't be recovered from price level.
  4. NO DATES      - sessions anonymized as Cxxx case ids.
  5. CANARIES      - 12 cases carry impossible features in 3 types
                     (or_range_pct < 0, or_pos = 99, rvol < 0); correct behavior
                     = FLAT/abstain. THE CANARY FLAG IS NOT SHOWN TO MODELS
                     (v2 caveat fix: v1 leaked a "canary" field in the payload).
                     Failing canaries = guessing without validating inputs.
  6. BASELINES     - scored against always-long / seeded-random (200-seed mean) /
                     pure-rule so a model must beat simple heuristics.
  7. DETERMINISTIC OUTCOMES - answers computed by this script in pure Python.
  8. V2 ADDITIONS  - 22-symbol universe (~740 cases, tighter CIs), payloads
                     chunked to stay well inside small-context models, split-half
                     period consistency, paired McNemar + paired netR sign test,
                     abstention-value analysis (what the skill avoided).

Subcommands:
  python blind_eval.py build     # fetch data, mask, write cases/answers
  python blind_eval.py prompt    # render 4 prompt payloads (gemma/nemotron x skill/noskill)
  python blind_eval.py score     # score decisions_*.json against answers + baselines
"""
import argparse
import glob
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import data as D  # noqa: E402

SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "NVDA", "TSLA",
           "MSFT", "AMD", "META", "AMZN", "GLD",
           "NFLX", "JPM", "XOM", "UNH", "COST", "DIS", "BA", "INTC", "MU", "TLT"]
CANARY_TYPES = ["neg_range", "absurd_pos", "neg_rvol"]
F = lambda name: os.path.join(HERE, name)

SKILL_EXCERPT = """EVIDENCE-FIRST TRADING RULES (skill catalog summary):
- Tier A1 ORB: first 15 min forms opening range (OR). Trigger = 09:50 bar closing
  beyond OR high -> LONG, below OR low -> SHORT. Evidence: independent tests show
  ~46-54% direction hit rate; breakeven ~50% after costs => ONLY take trades when
  confirmation is strong; otherwise FLAT.
- Tier A2 PDH/PDL: prior-day high/low are Tier-A LEVELS but the entry edge is only
  Tier B. Price AT these levels is a reaction zone, not a direction. Prefer FLAT
  unless the ORB trigger also agrees.
- No setup => FLAT (the skill never trades without a Tier A/B trigger).
- Costs: 0.2-0.5% targets are eaten by spread+fees; high win-rate/small-R systems
  carry negative skew. Abstaining is a valid, evidence-sanctioned position.
Return ONLY a JSON object mapping case id -> LONG or SHORT or FLAT. No prose."""

NO_SKILL_PROMPT = """You are a day trader. For each case decide LONG, SHORT, or FLAT
for the next 60 minutes. Return ONLY a JSON object mapping case id -> LONG or SHORT
or FLAT. No prose."""


def wilson(wr, n, z=1.96):
    if n <= 0:
        return (0.0, 1.0)
    d = 1 + z * z / n
    c = wr + z * z / (2 * n)
    m = z * math.sqrt(wr * (1 - wr) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def build_cmd():
    rng = random.Random(20261116)
    order = SYMBOLS[:]
    rng.shuffle(order)
    mask = {sym: f"INST-{i+1:02d}" for i, sym in enumerate(order)}
    json.dump({v: k for k, v in mask.items()}, open(F("mapping.json"), "w"), indent=1)

    raw = {}
    for sym in SYMBOLS:
        try:
            raw[sym] = D.sessions(D.fetch_bars(sym, "5m", "60d"))
            print(f"fetched {sym}: {len(raw[sym])} sessions")
            time.sleep(0.4)
        except Exception as e:
            print(f"{sym}: FAILED {e}")

    cases, answers = [], {}
    for sym, sess in raw.items():
        keys = sorted(sess)
        for i in range(1, len(keys)):
            day, prev = sess[keys[i]], sess[keys[i - 1]]
            or_bars = [b for b in day if D.minutes_since_open(b) < 15]
            trig = next((b for b in day if D.minutes_since_open(b) == 15), None)
            if len(or_bars) < 3 or trig is None:
                continue
            prev_hi, prev_lo = max(b["h"] for b in prev), min(b["l"] for b in prev)
            prev_close = prev[-1]["c"]
            or_hi, or_lo = max(b["h"] for b in or_bars), min(b["l"] for b in or_bars)
            entry = trig["c"]
            or_rng = or_hi - or_lo
            if or_rng <= 0:
                continue
            # 60-min horizon bar
            hz = next((b for b in day if D.minutes_since_open(b) >= 75
                       and b["dt"] > trig["dt"]), None)
            if hz is None:
                continue
            # setup tag
            if entry > or_hi:
                tag, pdir = "ORB", "LONG"
            elif entry < or_lo:
                tag, pdir = "ORB", "SHORT"
            elif abs(prev_hi - entry) / entry <= 0.0010:
                tag, pdir = "PDH_PROX", "LONG"   # rule baseline: probe-high continuation
            elif abs(prev_lo - entry) / entry <= 0.0010:
                tag, pdir = "PDL_PROX", "SHORT"  # rule baseline: probe-low continuation
            else:
                tag, pdir = "NONE", "FLAT"
            # race outcome (same math as backtest_orb.py)
            stop = or_lo if pdir == "LONG" else or_hi if pdir == "SHORT" else entry
            risk = abs(entry - stop) if pdir in ("LONG", "SHORT") else 0.0
            risk_bp = risk / entry * 10000 if risk > 0 else 0.0
            after = [b for b in day if b["dt"] > trig["dt"]]
            if pdir == "FLAT":
                out, r = None, 0.0
            else:
                target = entry + (2 * risk if pdir == "LONG" else -2 * risk)
                out, r = "eod", None
                for b in after:
                    if pdir == "LONG":
                        if b["l"] <= stop:
                            out, r = "stop", -1.0
                            break
                        if b["h"] >= target:
                            out, r = "target", 2.0
                            break
                    else:
                        if b["h"] >= stop:
                            out, r = "stop", -1.0
                            break
                        if b["l"] <= target:
                            out, r = "target", 2.0
                            break
                if r is None:
                    px = after[-1]["c"]
                    r = (px - entry) * (1 if pdir == "LONG" else -1) / risk
            vol3 = sum(b["v"] for b in or_bars)
            avg3 = (sum(b["v"] for b in prev) / len(prev) * 3) or 1
            feat = {
                "setup_hint_is_absent": True,
                "or_pos": round((entry - or_lo) / or_rng, 3),
                "or_range_pct": round(or_rng / prev_close * 100, 3),
                "gap_pct": round((day[0]["o"] - prev_close) / prev_close * 100, 3),
                "pdh_dist_pct": round((prev_hi - entry) / entry * 100, 3),
                "pdl_dist_pct": round((prev_lo - entry) / entry * 100, 3),
                "rvol": round(vol3 / avg3, 2),
                "_tag": tag,
            }
            cases.append({"feat": feat, "pdir": pdir, "sym": sym,
                          "date": keys[i], "r": r, "risk_bp": risk_bp,
                          "dir60": "LONG" if hz["c"] > entry else
                                   "SHORT" if hz["c"] < entry else "FLAT"})

    # NONE downsample to <=40% of cases (seeded)
    none = [c for c in cases if c["feat"]["_tag"] == "NONE"]
    other = [c for c in cases if c["feat"]["_tag"] != "NONE"]
    keep = rng.sample(none, min(len(none), max(10, int(len(other) * 0.65))))
    pool = other + keep
    rng.shuffle(pool)

    # assign ids + inject canaries (3 types; the flag lives ONLY in answers.json,
    # never in the payload the models see)
    out_cases, out_answers = [], {}
    n_canary = 12
    canary_slots = {i: CANARY_TYPES[j % len(CANARY_TYPES)]
                    for j, i in enumerate(
                        rng.sample(range(len(pool)), min(n_canary, len(pool))))}
    for i, c in enumerate(pool):
        cid = f"C{i+1:03d}"
        feat = {k: v for k, v in c["feat"].items() if k != "_tag"}
        ctype = canary_slots.get(i)
        if ctype == "neg_range":
            feat["or_range_pct"] = -abs(feat["or_range_pct"]) - 0.01  # impossible
        elif ctype == "absurd_pos":
            feat["or_pos"] = 99.0  # entry 99 opening-ranges above the low: impossible
        elif ctype == "neg_rvol":
            feat["rvol"] = -1.0  # negative volume ratio: impossible
        feat["canary"] = ctype is not None
        feat["id"] = cid
        out_cases.append(feat)
        out_answers[cid] = {
            "symbol": c["sym"], "date": c["date"], "setup": c["feat"]["_tag"],
            "rule_dir": c["pdir"], "dir60": c["dir60"],
            "race_r": round(c["r"], 3), "risk_bp": round(c["risk_bp"], 2),
            "net10bp": round(c["r"] - (10 / c["risk_bp"] if c["risk_bp"] > 0 else 0), 3),
            "canary": ctype is not None, "canary_type": ctype,
        }
    json.dump(out_cases, open(F("cases.json"), "w"), indent=1)
    json.dump(out_answers, open(F("answers.json"), "w"), indent=1)
    print(f"\nbuilt {len(out_cases)} cases "
          f"({sum(c['canary'] for c in out_cases)} canaries), "
          f"tradeable={sum(1 for a in out_answers.values() if a['setup']!='NONE' and not a['canary'])}")
    return 0


def prompt_cmd():
    cases = json.load(open(F("cases.json")))
    # v2: 'canary' key deliberately EXCLUDED - models must detect impossible
    # features themselves, not read a label. 'setup' tag also excluded (it is
    # what the deterministic RULE baseline uses; models must infer from features).
    keys = ("id", "or_pos", "or_range_pct", "gap_pct", "pdh_dist_pct",
            "pdl_dist_pct", "rvol")
    slim = [{k: c[k] for k in keys} for c in cases]
    os.makedirs(F("prompts"), exist_ok=True)
    for old in glob.glob(F("prompts/payload_*.txt")):
        os.remove(old)
    # chunk so prompt+completion stays well inside small-context models
    n_chunks = max(1, math.ceil(len(slim) / 450))
    step = math.ceil(len(slim) / n_chunks)
    for cond, rules in (("skill", SKILL_EXCERPT), ("noskill", NO_SKILL_PROMPT)):
        for i in range(n_chunks):
            body = json.dumps(slim[i * step:(i + 1) * step], separators=(",", ":"))
            txt = (f"{rules}\n\nCASES (JSON array; all values are %/ratios, no prices, "
                   f"no symbols, no dates):\n{body}\n\n"
                   "Respond with the JSON object only.")
            open(F(f"prompts/payload_{cond}_{i+1}.txt"), "w").write(txt)
    print(f"wrote {n_chunks} payload part(s) per condition "
          f"({len(slim)} cases, {len(keys)} visible fields, canary flag hidden)")
    return 0


def score_cmd():
    answers = json.load(open(F("answers.json")))
    cases = {c["id"]: c for c in json.load(open(F("cases.json")))}
    trade_all = [cid for cid, a in answers.items()
                 if not a["canary"] and a["setup"] != "NONE"]
    dates = sorted({answers[cid]["date"] for cid in trade_all})
    mid_date = dates[len(dates) // 2] if dates else ""

    def evaluate(preds, name):
        trade_ids, none_ids, can_ids = [], [], []
        for cid, a in answers.items():
            if a["canary"]:
                can_ids.append(cid)
            elif a["setup"] == "NONE":
                none_ids.append(cid)
            else:
                trade_ids.append(cid)
        calls = [(cid, preds[cid]) for cid in trade_ids
                 if preds.get(cid, "FLAT") in ("LONG", "SHORT")]
        correct = sum(1 for cid, p in calls if p == answers[cid]["dir60"])
        abst = len(trade_ids) - len(calls)
        n_call = len(calls)
        wr = correct / n_call if n_call else 0.0
        lo, hi = wilson(wr, n_call)
        z = ((wr - 0.5) / math.sqrt(0.25 / n_call)) if n_call > 30 else None
        # split-half period consistency (first vs second half of the window)
        h1 = [(cid, p) for cid, p in calls if answers[cid]["date"] <= mid_date]
        h2 = [(cid, p) for cid, p in calls if answers[cid]["date"] > mid_date]
        acc_h1 = (sum(1 for cid, p in h1 if p == answers[cid]["dir60"]) / len(h1)
                  ) if h1 else None
        acc_h2 = (sum(1 for cid, p in h2 if p == answers[cid]["dir60"]) / len(h2)
                  ) if h2 else None
        # canary FLAT-rate broken down by canary type (flag hidden in v2)
        can_types = {}
        for cid in can_ids:
            t = answers[cid].get("canary_type") or "unknown"
            can_types.setdefault(t, []).append(preds.get(cid, "FLAT") == "FLAT")
        can_by_type = {t: round(sum(v) / len(v), 2)
                       for t, v in sorted(can_types.items())}
        # net R with 10bp slippage on calls (race outcome)
        # P&L uses the PREDICTED direction; race geometry was computed for the
        # rule direction, so a matching call gets net10bp and an opposite call
        # gets its mirror (same R geometry, reversed sign) - approximation, applied
        # symmetrically to every condition.
        net = 0.0
        for cid, p in calls:
            a = answers[cid]
            if a["setup"] == "NONE":
                continue
            rd = {"ORB": a["rule_dir"], "PDH_PROX": "LONG", "PDL_PROX": "SHORT"}[a["setup"]]
            if p == rd:
                net += a["net10bp"]
            else:
                # opposite-direction race approximated as mirror of same R geometry
                net -= a["net10bp"]
        net = net / n_call if n_call else 0.0
        none_flat = (sum(1 for cid in none_ids if preds.get(cid, "FLAT") == "FLAT")
                     / len(none_ids) if none_ids else None)
        can_flat = (sum(1 for cid in can_ids if preds.get(cid, "FLAT") == "FLAT")
                    / len(can_ids) if can_ids else None)
        longs = sum(1 for cid, p in calls if p == "LONG")
        return {"name": name, "n_calls": n_call, "abstain": abst,
                "dir_acc": round(wr, 4), "ci": [round(lo, 3), round(hi, 3)],
                "z_vs_50": round(z, 2) if z else None,
                "avg_netR_10bp": round(net, 4),
                "none_flat": none_flat, "canary_flat": can_flat,
                "long_bias": round(longs / n_call, 3) if n_call else None,
                "acc_h1": round(acc_h1, 4) if acc_h1 is not None else None,
                "acc_h2": round(acc_h2, 4) if acc_h2 is not None else None,
                "n_h1": len(h1), "n_h2": len(h2),
                "can_by_type": can_by_type}

    results = []
    # baselines
    always_long = {cid: ("FLAT" if a["canary"] else "LONG") for cid, a in answers.items()}
    rule = {}
    for cid, a in answers.items():
        if a["canary"]:
            rule[cid] = "FLAT"
        elif a["setup"] == "NONE":
            rule[cid] = "FLAT"
        else:
            rule[cid] = {"ORB": a["rule_dir"], "PDH_PROX": "LONG",
                         "PDL_PROX": "SHORT"}[a["setup"]]
    # random baseline: mean over 200 seeds (a single seed can be a tail draw;
    # seed-42 scored 36.9% vs sim p025=42.4% - an unlucky stream, not a result)
    rnd_runs = []
    for seed in range(200):
        r2 = random.Random(seed)
        rp = {cid: ("FLAT" if answers[cid]["canary"] else r2.choice(
            ["LONG", "SHORT", "FLAT"])) for cid in answers}
        rnd_runs.append(evaluate(rp, "rand"))
    agg = dict(rnd_runs[0])
    for k in ("n_calls", "abstain", "dir_acc", "avg_netR_10bp", "long_bias",
              "none_flat", "canary_flat"):
        vals = [r[k] for r in rnd_runs if r[k] is not None]
        agg[k] = round(sum(vals) / len(vals), 4) if vals else None
    agg["name"] = "BASELINE random (mean of 200 seeds)"
    agg["sd_dir_acc"] = round((sum((r["dir_acc"] - agg["dir_acc"]) ** 2
                                   for r in rnd_runs) / len(rnd_runs)) ** 0.5, 4)
    # 'CI' for this row = 95% band of per-seed accuracy (not a binomial CI)
    accs = sorted(r["dir_acc"] for r in rnd_runs)
    agg["ci"] = [round(accs[int(0.025 * len(accs))], 3),
                 round(accs[int(0.975 * len(accs)) - 1], 3)]
    results.append(evaluate(always_long, "BASELINE always-LONG"))
    results.append(agg)
    results.append(evaluate(rule, "BASELINE pure-rule (no LLM)"))

    model_preds = []
    for path in sorted(glob.glob(F("decisions_*.json"))):
        name = os.path.basename(path)[len("decisions_"):-len(".json")]
        preds = json.load(open(path))
        results.append(evaluate(preds, f"MODEL {name}"))
        model_preds.append((name, preds))

    w = max(len(r["name"]) for r in results)
    hdr = (f"{'condition':{w}s} {'calls':>5} {'abst':>4} {'dirAcc':>7} "
           f"{'95%CI':>13} {'netR@10bp':>10} {'noneFlat':>8} {'canary':>6}")
    print(hdr)
    for r in results:
        none_s = (f"{r['none_flat']:.0%}" if r["none_flat"] is not None else "-")
        can_s = (f"{r['canary_flat']:.0%}" if r["canary_flat"] is not None else "-")
        print(f"{r['name']:{w}s} {r['n_calls']:>5} {r['abstain']:>4} "
              f"{r['dir_acc']:>7.1%} {str(r['ci']):>13} "
              f"{r['avg_netR_10bp']:>+10.3f} {none_s:>8} {can_s:>6}")
    json.dump(results, open(F("score_report.json"), "w"), indent=1)

    # split-half period consistency (did the result hold across the window?)
    print(f"\nperiod split (median session {mid_date}) - dir acc first/second half:")
    for r in results:
        s1 = (f"{r['acc_h1']:.1%} (n={r['n_h1']})"
              if r.get("acc_h1") is not None else "-")
        s2 = (f"{r['acc_h2']:.1%} (n={r['n_h2']})"
              if r.get("acc_h2") is not None else "-")
        print(f"  {r['name']:<36} {s1:>18} | {s2:>18}")

    # canary compliance by type - flag is HIDDEN from models in v2
    print("\ncanary FLAT-rate by type (flag hidden from models):")
    for r in results:
        if r.get("can_by_type"):
            print(f"  {r['name']:<36} {r['can_by_type']}")

    # abstention value: mean netR@10bp of tradeable cases taken vs skipped
    # (skipped cases valued at the pure-rule direction = the deterministic
    # alternative you get without the model)
    print("\nabstention value (mean netR@10bp over tradeable cases):")
    all_rule = [answers[cid]["net10bp"] for cid in trade_all]
    print(f"  {'pure-rule (takes everything)':<28} n={len(all_rule):>3} "
          f"mean {sum(all_rule) / len(all_rule):+.3f}R")
    for name, preds in model_preds:
        taken, skipped = [], []
        for cid in trade_all:
            a = answers[cid]
            rd = {"ORB": a["rule_dir"], "PDH_PROX": "LONG",
                  "PDL_PROX": "SHORT"}[a["setup"]]
            p = preds.get(cid, "FLAT")
            if p in ("LONG", "SHORT"):
                taken.append(a["net10bp"] if p == rd else -a["net10bp"])
            else:
                skipped.append(a["net10bp"])
        t_m = sum(taken) / len(taken) if taken else float("nan")
        s_m = sum(skipped) / len(skipped) if skipped else float("nan")
        print(f"  {name:<28} taken n={len(taken):>3} mean {t_m:+.3f}R | "
              f"skipped n={len(skipped):>3} mean {s_m:+.3f}R")

    # paired skill-vs-noskill test within each model (exact binomial on
    # cases both conditions actually called)
    print()
    bases = sorted({os.path.basename(p)[len("decisions_"):].rsplit("_", 1)[0]
                    for p in glob.glob(F("decisions_*.json"))})
    for base in bases:
        try:
            s = json.load(open(F(f"decisions_{base}_skill.json")))
            n = json.load(open(F(f"decisions_{base}_noskill.json")))
        except FileNotFoundError:
            continue
        both = [cid for cid, a in answers.items()
                if not a["canary"] and a["setup"] != "NONE"
                and s.get(cid) in ("LONG", "SHORT")
                and n.get(cid) in ("LONG", "SHORT")]
        b = sum(1 for cid in both
                if s[cid] == answers[cid]["dir60"] and n[cid] != answers[cid]["dir60"])
        c_ = sum(1 for cid in both
                 if n[cid] == answers[cid]["dir60"] and s[cid] != answers[cid]["dir60"])
        m = b + c_
        if m == 0:
            p = 1.0
        else:
            k = min(b, c_)
            p = min(1.0, 2 * sum(math.comb(m, i) for i in range(k + 1)) / 2 ** m)
        print(f"paired {base}: both-called n={len(both)}, skill-only-right={b}, "
              f"noskill-only-right={c_}, exact McNemar p={p:.3f}")
        # paired netR sign test on the same cases (skill call vs noskill call)
        diffs = []
        for cid in both:
            a = answers[cid]
            rd = {"ORB": a["rule_dir"], "PDH_PROX": "LONG",
                  "PDL_PROX": "SHORT"}[a["setup"]]
            vs = a["net10bp"] if s[cid] == rd else -a["net10bp"]
            vn = a["net10bp"] if n[cid] == rd else -a["net10bp"]
            diffs.append(vs - vn)
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        m2 = pos + neg
        if m2:
            p2 = min(1.0, 2 * sum(math.comb(m2, i)
                                  for i in range(min(pos, neg) + 1)) / 2 ** m2)
        else:
            p2 = 1.0
        print(f"  netR sign test on those cases: skill ahead on {pos}, "
              f"noskill ahead on {neg}, ties {len(diffs) - m2}, exact p={p2:.3f}")
    print("\nwrote score_report.json")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["build", "prompt", "score"])
    a = p.parse_args()
    return {"build": build_cmd, "prompt": prompt_cmd, "score": score_cmd}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
