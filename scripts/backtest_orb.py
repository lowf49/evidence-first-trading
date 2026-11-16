"""Deterministic historical validation of the skill's Tier-A setups.

Parts:
  A1  Opening Range Breakout (exact catalog rules) on 5m data (<=60d, Yahoo limit)
  A2  PDH/PDL touch statistics on daily data (10y) - large n
  A3  Intraday momentum: sign(09:30-15:30) vs final 30 min, on 5m data
  +   slippage sweep 0/5/10/20/50bp on A1 (mandatory per cost-math.md)

Usage: python backtest_orb.py [--symbols SPY,QQQ,...] [--daily-years 10]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "evaluation", "backtest_results.json")
DEFAULTS = ("SPY,QQQ,IWM,DIA,AAPL,NVDA,TSLA,MSFT,AMD,META,AMZN,GLD,"
            "NFLX,JPM,XOM,UNH,COST,DIS,BA,INTC,MU,TLT")


def first3_or(bars):
    or_bars = [b for b in bars if D.minutes_since_open(b) < 15]
    trig = next((b for b in bars if D.minutes_since_open(b) == 15), None)
    if len(or_bars) < 3 or trig is None:
        return None
    return (max(b["h"] for b in or_bars), min(b["l"] for b in or_bars), trig)


def race_outcome(bars_after, entry, direction, stop, target):
    """Return (outcome, exit_price): 'target'|'stop'|'eod'."""
    for b in bars_after:
        if direction == "LONG":
            if b["l"] <= stop:
                return ("stop", stop)
            if b["h"] >= target:
                return ("target", target)
        else:
            if b["h"] >= stop:
                return ("stop", stop)
            if b["l"] <= target:
                return ("target", target)
    return ("eod", bars_after[-1]["c"]) if bars_after else (None, entry)


def backtest_a1(symbols, slippage_bps=(0, 5, 10, 20, 50)):
    trades = []
    for sym in symbols:
        try:
            bars = D.sessions(D.fetch_bars(sym, "5m", "60d"))
        except Exception as e:
            print(f"  A1 {sym}: fetch failed {e}")
            continue
        keys = sorted(bars)
        for i in range(1, len(keys)):
            sess = bars[keys[i]]
            o = first3_or(sess)
            if not o:
                continue
            or_hi, or_lo, trig = o
            e = trig["c"]
            if e > or_hi:
                d = "LONG"
            elif e < or_lo:
                d = "SHORT"
            else:
                continue
            stop = or_lo if d == "LONG" else or_hi
            risk = abs(e - stop)
            if risk <= 0:
                continue
            target = e + (2 * risk if d == "LONG" else -2 * risk)
            after = [b for b in sess if b["dt"] > trig["dt"]]
            out, px = race_outcome(after, e, d, stop, target)
            if out is None:
                continue
            r_gross = (px - e) * (1 if d == "LONG" else -1) / risk
            risk_bp = risk / e * 10000
            trades.append({
                "sym": sym, "date": keys[i], "dir": d, "r_gross": r_gross,
                "outcome": out, "risk_bp": risk_bp,
                "net": {f"{s}bp": r_gross - (s / risk_bp if risk_bp > 0 else 0)
                        for s in slippage_bps},
            })
    return trades


def backtest_a1_hourly(symbols, slippage_bps=(0, 5, 10, 20, 50),
                       exclude_recent_days=60):
    """A1 rules on 60m bars over an OLDER, non-overlapping window (period
    robustness check): OR = first hourly bar of the session, trigger = second
    bar's close, same stop/target geometry. Only sessions older than
    exclude_recent_days are used, so this never overlaps A1's <=60d 5m window."""
    cutoff = time.time() - exclude_recent_days * 86400
    trades = []
    for sym in symbols:
        try:
            bars = D.sessions(D.fetch_bars(sym, "60m", "730d"))
        except Exception as e:
            print(f"  A1b {sym}: fetch failed {e}")
            continue
        for key, sess in sorted(bars.items()):
            if len(sess) < 3 or sess[0]["dt"] >= cutoff:
                continue
            or_b, trig = sess[0], sess[1]
            or_hi, or_lo = or_b["h"], or_b["l"]
            e = trig["c"]
            if e > or_hi:
                d = "LONG"
            elif e < or_lo:
                d = "SHORT"
            else:
                continue
            stop = or_lo if d == "LONG" else or_hi
            risk = abs(e - stop)
            if risk <= 0:
                continue
            target = e + (2 * risk if d == "LONG" else -2 * risk)
            after = [b for b in sess if b["dt"] > trig["dt"]]
            out, px = race_outcome(after, e, d, stop, target)
            if out is None:
                continue
            r_gross = (px - e) * (1 if d == "LONG" else -1) / risk
            risk_bp = risk / e * 10000
            trades.append({
                "sym": sym, "date": key, "dir": d, "r_gross": r_gross,
                "outcome": out, "risk_bp": risk_bp,
                "net": {f"{s}bp": r_gross - (s / risk_bp if risk_bp > 0 else 0)
                        for s in slippage_bps},
            })
    return trades


def backtest_a2(symbols, years=10):
    stats = {"n_sessions": 0, "touch_high": 0, "touch_low": 0, "touch_any": 0,
             "touch_both": 0}
    for sym in symbols:
        try:
            bars = D.fetch_bars(sym, "1d", f"{years}y")
        except Exception as e:
            print(f"  A2 {sym}: fetch failed {e}")
            continue
        prev = None
        for b in bars:
            if prev:
                # clean touch test: level value inside the day's range
                th = b["l"] <= prev["h"] <= b["h"]
                tl = b["l"] <= prev["l"] <= b["h"]
                stats["n_sessions"] += 1
                stats["touch_high"] += int(th)
                stats["touch_low"] += int(tl)
                stats["touch_any"] += int(th or tl)
                stats["touch_both"] += int(th and tl)
            prev = b
    return stats


def backtest_a3(symbols):
    n = hit = n_up = n_dn = 0
    for sym in symbols:
        try:
            bars = D.sessions(D.fetch_bars(sym, "5m", "60d"))
        except Exception as e:
            print(f"  A3 {sym}: fetch failed {e}")
            continue
        for key, sess in bars.items():
            pre = [b for b in sess if D.minutes_since_open(b) <= 360]   # ..15:30
            post = [b for b in sess if D.minutes_since_open(b) > 360]   # 15:30-16:00
            if len(pre) < 10 or len(post) < 3:
                continue
            r1 = pre[-1]["c"] - sess[0]["o"]
            r2 = post[-1]["c"] - post[0]["o"]
            if r1 == 0 or r2 == 0:
                continue
            n += 1
            hit += int((r1 > 0) == (r2 > 0))
            n_up += int(r1 > 0)
            n_dn += int(r1 < 0)
    return {"n": n, "accuracy": hit / n if n else None,
            "n_pred_up": n_up, "n_pred_dn": n_dn}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default=DEFAULTS)
    p.add_argument("--daily-years", type=int, default=10)
    a = p.parse_args()
    syms = [s.strip().upper() for s in a.symbols.split(",") if s.strip()]

    print(f"A1 ORB backtest (5m, 60d, {len(syms)} symbols)...")
    trades = backtest_a1(syms)
    n = len(trades)
    if n:
        wr = sum(t["r_gross"] > 0 for t in trades) / n
        exp_gross = sum(t["r_gross"] for t in trades) / n
        print(f"  trades={n}  WR={wr:.1%}  expectancy(gross)={exp_gross:+.3f}R")
        for s in (0, 5, 10, 20, 50):
            e = sum(t["net"][f"{s}bp"] for t in trades) / n
            print(f"  slippage {s:>2}bp : expectancy {e:+.3f}R/trade  "
                  f"({'POSITIVE' if e > 0 else 'NEGATIVE'})")
        by_dir = {d: [t for t in trades if t["dir"] == d] for d in ("LONG", "SHORT")}
        for d, ts in by_dir.items():
            if ts:
                print(f"  {d}: n={len(ts)} WR={sum(t['r_gross'] > 0 for t in ts)/len(ts):.1%}")
    else:
        print("  no ORB triggers in window")

    print(f"A1b hourly ORB, older window (60-730d ago, {len(syms)} symbols)...")
    trades_b = backtest_a1_hourly(syms)
    nb = len(trades_b)
    if nb:
        wr_b = sum(t["r_gross"] > 0 for t in trades_b) / nb
        print(f"  trades={nb}  WR={wr_b:.1%}  "
              f"expectancy(gross)={sum(t['r_gross'] for t in trades_b) / nb:+.3f}R")
        for s in (0, 5, 10, 20, 50):
            e = sum(t["net"][f"{s}bp"] for t in trades_b) / nb
            print(f"  slippage {s:>2}bp : expectancy {e:+.3f}R/trade  "
                  f"({'POSITIVE' if e > 0 else 'NEGATIVE'})")
        for d in ("LONG", "SHORT"):
            ts = [t for t in trades_b if t["dir"] == d]
            if ts:
                print(f"  {d}: n={len(ts)} "
                      f"WR={sum(t['r_gross'] > 0 for t in ts) / len(ts):.1%}")
    else:
        print("  no hourly ORB triggers in older window")

    print(f"A2 PDH/PDL touch stats (1d, {a.daily_years}y, {len(syms)} symbols)...")
    a2 = backtest_a2(syms, a.daily_years)
    if a2["n_sessions"]:
        for k in ("touch_high", "touch_low", "touch_any", "touch_both"):
            print(f"  {k:11s}: {a2[k]/a2['n_sessions']:.1%} (n={a2['n_sessions']})")

    print("A3 last-30-min momentum (5m, 60d)...")
    a3 = backtest_a3(syms)
    if a3["n"]:
        print(f"  sign accuracy={a3['accuracy']:.1%} (n={a3['n']}, "
              f"up-pred={a3['n_pred_up']}, dn-pred={a3['n_pred_dn']})")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": int(time.time()), "symbols": syms, "A1": trades,
                   "A1b": trades_b, "A2": a2, "A3": a3}, f, indent=1)
    print(f"wrote {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
