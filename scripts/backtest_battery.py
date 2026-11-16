"""Pre-registered candidate battery — see evaluation/PRE-REGISTER.md.

Runs every candidate exactly as frozen. No parameter may be changed to improve
results; changes are amendments and must be logged there.

Data: Yahoo Finance, keyless (via scripts/data.py). Cached to evaluation/cache/.

Usage: python scripts/backtest_battery.py [--only C1,C2] [--symbols SPY,QQQ]
"""
import argparse
import datetime as dt
import json
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "..", "evaluation", "cache")
OUT = os.path.join(HERE, "..", "evaluation", "battery_results.json")
DEFAULTS = ("SPY,QQQ,IWM,DIA,AAPL,NVDA,TSLA,MSFT,AMD,META,AMZN,GLD,"
            "NFLX,JPM,XOM,UNH,COST,DIS,BA,INTC,MU,TLT")
COSTS = (0, 5, 10, 20, 50)  # bp of notional per side (round trip encoded as cost)


def cached_fetch(symbol, interval, range_):
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = f"{symbol}_{interval}_{range_}.json".replace("/", "_")
    path = os.path.join(CACHE_DIR, key)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    bars = D.fetch_bars(symbol, interval, range_)
    with open(path, "w") as f:
        json.dump(bars, f)
    return bars


def day_view(sess_bars):
    return {"open": sess_bars[0]["o"], "high": max(b["h"] for b in sess_bars),
            "low": min(b["l"] for b in sess_bars),
            "close": sess_bars[-1]["c"]}


def race(bars, entry_idx, direction, stop, target):
    for b in bars[entry_idx + 1:]:
        if direction == "LONG":
            if b["l"] <= stop:
                return "stop", stop
            if target is not None and b["h"] >= target:
                return "target", target
        else:
            if b["h"] >= stop:
                return "stop", stop
            if target is not None and b["l"] <= target:
                return "target", target
    last = bars[-1]
    return "eod", last["c"]


def r_multiple(entry, px, direction, risk_price):
    if direction == "LONG":
        return (px - entry) / risk_price
    return (entry - px) / risk_price


def wilson(wins, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = wins / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - half) / den, p, (centre + half) / den)


def normal_p_two_tailed(t):
    return math.erfc(abs(t) / math.sqrt(2))


def summarize(trades, label):
    if not trades:
        return {"label": label, "n": 0}
    rs = [t["r_gross"] for t in trades]
    n = len(rs)
    wins = sum(1 for r in rs if r > 0)
    mean = statistics.fmean(rs)
    sd = statistics.stdev(rs) if n > 1 else 0.0
    nets = {}
    for bp in COSTS:
        vals = []
        for t in trades:
            risk_bp = t["risk_price"] / t["entry"] * 10000
            vals.append(t["r_gross"] - (bp / risk_bp if risk_bp else 0.0))
        nets[f"{bp}bp"] = {"mean": statistics.fmean(vals),
                          "positive": statistics.fmean(vals) > 0}
    t = mean / (sd / math.sqrt(n)) if sd > 0 else 0.0
    p = normal_p_two_tailed(t)
    gross_win = sum(r for r in rs if r > 0)
    gross_loss = -sum(r for r in rs if r < 0)
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    eq = 0.0
    peak = 0.0
    maxdd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        maxdd = max(maxdd, peak - eq)
    lo, p_hat, hi = wilson(wins, n)
    ds = sorted(t["date"] for t in trades)
    med = ds[len(ds) // 2]
    halves = {}
    for name, subset in (("first", [t for t in trades if t["date"] <= med]),
                         ("second", [t for t in trades if t["date"] > med])):
        halves[name] = statistics.fmean(t["r_gross"] for t in subset) if subset else None
    same_sign = (halves["first"] is not None and halves["second"] is not None
                 and (halves["first"] >= 0) == (halves["second"] >= 0))
    half = 1.96 * sd / math.sqrt(n) if n > 1 else 0.0
    return {
        "label": label, "n": n, "wins": wins, "wr": p_hat,
        "wr_ci": [lo, hi], "expectancy": mean,
        "sd": sd, "t": t, "p": p, "ci_mean": [mean - half, mean + half],
        "profit_factor": pf, "max_drawdown_R": maxdd,
        "net": nets, "subperiods": halves, "subperiod_same_sign": same_sign,
    }


def add_trade(trades, label, sym, date, direction, entry, stop, exit_px,
              risk_price=None, outcome=""):
    if risk_price is None:
        risk_price = abs(entry - stop)
    if risk_price <= 0:
        return
    trades.append({"strat": label, "sym": sym, "date": date, "dir": direction,
                    "entry": entry, "stop": stop, "exit": exit_px,
                    "risk_price": risk_price,
                    "r_gross": r_multiple(entry, exit_px, direction, risk_price),
                    "outcome": outcome})


def c1_orb(sessions5, sessions60, older60_only=False):
    out = []
    for dataset, sess_dict in (("W5m", sessions5), ("W60m", sessions60)):
        if older60_only and dataset == "W60m":
            cutoff = time.time() - 60 * 86400
        else:
            cutoff = None
        for sym, sess in sess_dict.items():
            keys = sorted(sess)
            for key in keys:
                bars = sess[key]
                if dataset == "W5m":
                    or_bars = [b for b in bars if D.minutes_since_open(b) < 15]
                    trig = next((b for b in bars if D.minutes_since_open(b) == 15), None)
                    if len(or_bars) < 3 or trig is None:
                        continue
                    or_hi = max(b["h"] for b in or_bars)
                    or_lo = min(b["l"] for b in or_bars)
                    e = trig["c"]
                    t_idx = bars.index(trig)
                else:
                    if len(bars) < 2:
                        continue
                    or_b, trig = bars[0], bars[1]
                    if cutoff and or_b["dt"] >= cutoff:
                        continue
                    or_hi, or_lo = or_b["h"], or_b["l"]
                    e = trig["c"]
                    t_idx = 1
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
                target = e + 2 * risk if d == "LONG" else e - 2 * risk
                outc, px = race(bars, t_idx, d, stop, target)
                add_trade(out, "C1", sym, key, d, e, stop, px, risk, outc)
    return out


def pdh_trades(sessions5, sessions60):
    c2, c3 = [], []
    for dataset, sess_dict in (("W5m", sessions5), ("W60m", sessions60)):
        for sym, sess in sess_dict.items():
            keys = sorted(sess)
            prev_view = None
            for key in keys:
                bars = sess[key]
                view = day_view(bars)
                if prev_view is None:
                    prev_view = view
                    continue
                pdh, pdl = prev_view["high"], prev_view["low"]
                prev_range = pdh - pdl
                if prev_range <= 0:
                    prev_view = view
                    continue
                first15 = [b for b in bars if D.minutes_since_open(b) < 15]
                pdh_touched = any(b["h"] >= pdh for b in first15)
                pdl_touched = any(b["l"] <= pdl for b in first15)
                if dataset == "W5m":
                    entry_bar = next((b for b in bars if D.minutes_since_open(b) == 60), None)
                    if entry_bar is None:
                        prev_view = view
                        continue
                    eidx = bars.index(entry_bar)
                else:
                    if len(bars) < 2:
                        prev_view = view
                        continue
                    entry_bar = bars[1]
                    eidx = 1
                so_far = bars[:eidx + 1]
                hi_so_far = max(b["h"] for b in so_far)
                lo_so_far = min(b["l"] for b in so_far)
                c3_done = False
                for j, b in enumerate(bars):
                    m = D.minutes_since_open(b)
                    if m <= 120 and not c3_done:
                        if b["h"] >= pdh and (j == 0 or bars[j - 1]["h"] < pdh):
                            e = b["c"]
                            stop = pdh + 0.1 * prev_range
                            outc, px = race(bars, j, "SHORT", stop, view["open"])
                            add_trade(c3, "C3", sym, key, "SHORT", e, stop, px,
                                      abs(e - stop), outc)
                            c3_done = True
                        elif b["l"] <= pdl and (j == 0 or bars[j - 1]["l"] > pdl):
                            e = b["c"]
                            stop = pdl - 0.1 * prev_range
                            outc, px = race(bars, j, "LONG", stop, view["open"])
                            add_trade(c3, "C3", sym, key, "LONG", e, stop, px,
                                      abs(e - stop), outc)
                            c3_done = True
                if not pdh_touched and hi_so_far > pdh and entry_bar["c"] > pdh:
                    e = entry_bar["c"]
                    stop = pdh
                    risk = abs(e - stop)
                    if risk > 0:
                        target = e + 2 * risk
                        outc, px = race(bars, eidx, "LONG", stop, target)
                        add_trade(c2, "C2", sym, key, "LONG", e, stop, px, risk, outc)
                if not pdl_touched and lo_so_far < pdl and entry_bar["c"] < pdl:
                    e = entry_bar["c"]
                    stop = pdl
                    risk = abs(e - stop)
                    if risk > 0:
                        target = e - 2 * risk
                        outc, px = race(bars, eidx, "SHORT", stop, target)
                        add_trade(c2, "C2", sym, key, "SHORT", e, stop, px, risk, outc)
                prev_view = view
    return c2, c3


def gap_trades(sessions5, sessions60):
    c4, c5 = [], []
    for dataset, sess_dict in (("W5m", sessions5), ("W60m", sessions60)):
        for sym, sess in sess_dict.items():
            keys = sorted(sess)
            prev_close = None
            for key in keys:
                bars = sess[key]
                view = day_view(bars)
                if prev_close is None:
                    prev_close = view["close"]
                    continue
                gap = view["open"] - prev_close
                gap_pct = gap / prev_close * 100
                if abs(gap_pct) >= 0.5:
                    if dataset == "W5m":
                        trig = next((b for b in bars if D.minutes_since_open(b) == 15), None)
                        confirm_idx = bars.index(trig) if trig else None
                        if trig is None:
                            prev_close = view["close"]
                            continue
                        e = trig["c"]
                        held_up = e >= view["open"]
                        held_dn = e <= view["open"]
                    else:
                        trig = bars[0]
                        confirm_idx = 0
                        e = trig["c"]
                        held_up = e >= view["open"]
                        held_dn = e <= view["open"]
                    if gap_pct >= 0.5:
                        d_4 = "LONG"
                        ok = held_up
                    else:
                        d_4 = "SHORT"
                        ok = held_dn
                    if ok:
                        stop = view["open"]
                        risk = abs(e - stop)
                        if risk > 0:
                            target = e + 2 * risk if d_4 == "LONG" else e - 2 * risk
                            outc, px = race(bars, confirm_idx, d_4, stop, target)
                            add_trade(c4, "C4", sym, key, d_4, e, stop, px, risk, outc)
                        d_5 = "SHORT" if d_4 == "LONG" else "LONG"
                        stop5 = (trig["h"] if d_4 == "LONG" else trig["l"])
                        risk5 = abs(e - stop5)
                        if risk5 > 0:
                            outc, px = race(bars, confirm_idx, d_5, stop5, view["open"])
                            add_trade(c5, "C5", sym, key, d_5, e, stop5, px, risk5, outc)
                prev_close = view["close"]
    return c4, c5


def c6_opening_drive(sessions5):
    out = []
    for sym, sess in sessions5.items():
        keys = sorted(sess)
        prev_range = None
        prev_close = None
        for key in keys:
            bars = sess[key]
            view = day_view(bars)
            if prev_range is None or prev_close is None:
                prev_range = view["high"] - view["low"]
                prev_close = view["close"]
                continue
            trig = next((b for b in bars if D.minutes_since_open(b) == 15), None)
            if trig is None:
                prev_range = view["high"] - view["low"]
                prev_close = view["close"]
                continue
            drive = trig["c"] - prev_close
            tidx = bars.index(trig)
            if prev_range > 0 and abs(drive) >= 0.6 * prev_range:
                if drive > 0:
                    d, stop = "SHORT", trig["h"]
                else:
                    d, stop = "LONG", trig["l"]
                e = trig["c"]
                risk = abs(e - stop)
                if risk > 0:
                    outc, px = race(bars, tidx, d, stop, view["open"])
                    add_trade(out, "C6", sym, key, d, e, stop, px, risk, outc)
            prev_range = view["high"] - view["low"]
            prev_close = view["close"]
    return out


def c7_lunch(sessions5):
    out = []
    for sym, sess in sessions5.items():
        for key, bars in sess.items():
            morning = [b for b in bars if D.minutes_since_open(b) <= 150]
            lb = [b for b in bars if D.minutes_since_open(b) == 150]
            exitb = [b for b in bars if D.minutes_since_open(b) == 240]
            if len(morning) < 10 or not lb or not exitb:
                continue
            e = lb[0]["c"]
            m_high = max(b["h"] for b in morning)
            m_low = min(b["l"] for b in morning)
            d = "SHORT" if e > morning[0]["o"] else "LONG"
            stop = m_high if d == "SHORT" else m_low
            risk = abs(e - stop)
            if risk <= 0:
                continue
            stopped_px = None
            for b in bars:
                m = D.minutes_since_open(b)
                if m <= 150 or m > 240:
                    continue
                if d == "SHORT" and b["h"] >= stop:
                    stopped_px = stop
                    break
                if d == "LONG" and b["l"] <= stop:
                    stopped_px = stop
                    break
            px = stopped_px if stopped_px is not None else exitb[0]["c"]
            add_trade(out, "C7", sym, key, d, e, stop, px, risk,
                      "stop" if stopped_px is not None else "time")
    return out


def c8_first_hour(sessions60):
    out = []
    for sym, sess in sessions60.items():
        for key, bars in sess.items():
            if len(bars) < 2:
                continue
            fb = bars[0]
            d = "LONG" if fb["c"] >= fb["o"] else "SHORT"
            e = fb["c"]
            stop = fb["l"] if d == "LONG" else fb["h"]
            risk = abs(e - stop)
            if risk <= 0:
                continue
            target = e + 2 * risk if d == "LONG" else e - 2 * risk
            outc, px = race(bars, 0, d, stop, target)
            add_trade(out, "C8", sym, key, d, e, stop, px, risk, outc)
    return out


def c9_last30fade(sessions60):
    out = []
    cutoff = time.time() - 60 * 86400
    for sym, sess in sessions60.items():
        for key, bars in sess.items():
            if len(bars) < 6 or bars[0]["dt"] >= cutoff:
                continue
            trig = None
            for b in bars:
                if D.minutes_since_open(b) == 300:
                    trig = b
                    break
            if trig is None:
                continue
            e = trig["c"]
            d = "SHORT" if e >= bars[0]["o"] else "LONG"
            stop = trig["h"] if d == "SHORT" else trig["l"]
            risk = abs(e - stop)
            if risk <= 0:
                continue
            exit_bar = next((b for b in bars if D.minutes_since_open(b) == 360), None)
            if exit_bar is None:
                continue
            px = exit_bar["c"]
            if d == "SHORT" and exit_bar["h"] >= stop:
                px = stop
            elif d == "LONG" and exit_bar["l"] <= stop:
                px = stop
            add_trade(out, "C9", sym, key, d, e, stop, px, risk, "time_or_stop")
    return out


def c11_nr7(daily):
    out = []
    for sym, bars in daily.items():
        ranges = [b["h"] - b["l"] for b in bars]
        for i in range(7, len(bars) - 1):
            today = bars[i]
            rng = today["h"] - today["l"]
            if rng <= 0:
                continue
            if rng >= min(ranges[i - 6:i]):
                continue
            nxt = bars[i + 1]
            if nxt["c"] > today["h"]:
                d = "LONG"
                stop = today["l"]
            elif nxt["c"] < today["l"]:
                d = "SHORT"
                stop = today["h"]
            else:
                continue
            e = nxt["c"]
            risk = abs(e - stop)
            if risk <= 0 or i + 2 >= len(bars):
                continue
            exit_bar = bars[i + 2]
            px = exit_bar["c"]
            if d == "LONG" and exit_bar["l"] <= stop:
                px = stop
            elif d == "SHORT" and exit_bar["h"] >= stop:
                px = stop
            add_trade(out, "C11", sym,
                      dt.datetime.fromtimestamp(bars[i + 1]["dt"], dt.timezone.utc).date().isoformat(),
                      d, e, stop, px, risk, "1d_hold")
    return out


def c12_close_drift(daily):
    out = []
    for sym, bars in daily.items():
        for i in range(len(bars) - 2):
            b = bars[i]
            rng = b["h"] - b["l"]
            if rng <= 0:
                continue
            pos = (b["c"] - b["l"]) / rng
            if pos >= 0.8:
                d = "LONG"
            elif pos <= 0.2:
                d = "SHORT"
            else:
                continue
            nxt = bars[i + 1]
            e = nxt["o"]
            risk = rng
            px = nxt["c"]
            add_trade(out, "C12", sym,
                      dt.datetime.fromtimestamp(nxt["dt"], dt.timezone.utc).date().isoformat(),
                      d, e, e - risk if d == "LONG" else e + risk, px, risk, "1d")
    return out


def c13_crypto(sessions60):
    out = []
    for sym in ("BTC-USD", "ETH-USD"):
        bars = sessions60.get(sym)
        if not bars:
            syms_bars = cached_fetch(sym, "60m", "730d")
            bars = syms_bars
        in_pos_until = -1
        rows = bars if isinstance(bars, list) else [b for b in bars]
        for i in range(4, len(rows)):
            if i <= in_pos_until:
                continue
            ret4 = (rows[i]["c"] / rows[i - 4]["o"]) - 1
            if abs(ret4) < 0.01:
                continue
            d = "SHORT" if ret4 > 0 else "LONG"
            e = rows[i]["c"]
            risk = 0.01 * e
            exit_idx = min(i + 4, len(rows) - 1)
            px = rows[exit_idx]["c"]
            add_trade(out, "C13", sym,
                      dt.datetime.fromtimestamp(rows[i]["dt"], dt.timezone.utc).date().isoformat(),
                      d, e, e - risk if d == "LONG" else e + risk, px, risk, "fixed4")
            in_pos_until = exit_idx
    return out


def c15_xsec(daily):
    out = []
    per_sym = {}
    for sym, bars in daily.items():
        m = {dt.datetime.fromtimestamp(b["dt"], dt.timezone.utc).date().isoformat(): b for b in bars}
        per_sym[sym] = m
    if not per_sym:
        return out
    all_dates = sorted({d for m in per_sym.values() for d in m})
    date_idx = {d: i for i, d in enumerate(all_dates)}
    for d_idx, day in enumerate(all_dates):
        if d_idx == 0:
            continue
        prev = all_dates[d_idx - 1]
        oi = date_idx[prev]
        if oi == 0:
            continue
        pp = all_dates[oi - 1]
        ents = []
        for sym, m in per_sym.items():
            if day in m and prev in m and pp in m:
                prev_b, cur_b = m[prev], m[day]
                prev_ret = prev_b["c"] / m[pp]["c"] - 1
                ents.append((sym, prev_ret, prev_b, cur_b))
        if len(ents) < 12:
            continue
        ents.sort(key=lambda x: x[1])
        q = len(ents) // 4
        shorts = ents[:q]
        longs = ents[-q:]
        rs = []
        med_rng = statistics.median((e[2]["h"] - e[2]["l"]) / e[2]["c"] for e in ents)
        for sym, pr, prev_b, cur_b in longs + shorts:
            is_long = (sym, pr, prev_b, cur_b) in longs
            day_pct = (cur_b["c"] - cur_b["o"]) / cur_b["o"] * (1 if is_long else -1)
            rs.append(day_pct)
        if rs and med_rng > 0:
            spread = statistics.fmean(rs)
            r = spread / med_rng
            entry = 1.0
            stop = entry - med_rng
            add_trade(out, "C15", "UNIVERSE", day, "LONG", entry, stop,
                      entry + r * med_rng, med_rng, "xsec")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default=DEFAULTS)
    p.add_argument("--only", default="")
    a = p.parse_args()
    syms = [s.strip().upper() for s in a.symbols.split(",") if s.strip()]
    only = {s.strip().upper() for s in a.only.split(",") if s.strip()}

    print(f"fetching data ({len(syms)} symbols)...")
    sessions5, sessions60, daily = {}, {}, {}
    for sym in syms:
        try:
            bars5 = cached_fetch(sym, "5m", "60d")
            sessions5[sym] = D.sessions(bars5)
        except Exception as e:
            print(f"  5m {sym}: {e}")
        try:
            bars60 = cached_fetch(sym, "60m", "730d")
            sessions60[sym] = D.sessions(bars60)
        except Exception as e:
            print(f"  60m {sym}: {e}")
        try:
            daily[sym] = cached_fetch(sym, "1d", "10y")
        except Exception as e:
            print(f"  1d {sym}: {e}")
    crypto60 = {}
    for sym in ("BTC-USD", "ETH-USD"):
        try:
            crypto60[sym] = cached_fetch(sym, "60m", "730d")
        except Exception as e:
            print(f"  crypto {sym}: {e}")

    results = []

    def run(label, fn):
        if only and not any(x in label for x in only):
            return
        print(f"{label} ...")
        t0 = time.time()
        trades = fn()
        summary = summarize(trades, label)
        summary["elapsed_s"] = round(time.time() - t0, 1)
        results.append(summary)

    run("C1 (5m, recent 60d)", lambda: c1_orb(sessions5, sessions60, older60_only=False))
    run("C1 (60m, older)", lambda: [t for t in c1_orb({}, sessions60, older60_only=True)] )
    c2, c3 = pdh_trades(sessions5, sessions60)
    run("C2 (PDH breakout)", lambda: c2)
    run("C3 (PDH fade)", lambda: c3)
    c4, c5 = gap_trades(sessions5, sessions60)
    run("C4 (gap-and-go)", lambda: c4)
    run("C5 (gap fade)", lambda: c5)
    run("C6 (opening-drive fade)", lambda: c6_opening_drive(sessions5))
    run("C7 (lunch reversion)", lambda: c7_lunch(sessions5))
    run("C8 (first-hour continuation)", lambda: c8_first_hour(sessions60))
    run("C9 (last-30 fade, older 60m)", lambda: c9_last30fade(sessions60))
    run("C11 (NR7)", lambda: c11_nr7(daily))
    run("C12 (close drift)", lambda: c12_close_drift(daily))
    run("C13 (crypto 4h reversal)", lambda: c13_crypto(crypto60))
    run("C15 (cross-sectional RS)", lambda: c15_xsec(daily))

    with open(OUT, "w") as f:
        json.dump({"run": int(time.time()), "symbols": syms, "candidates": results},
                  f, indent=1)
    print("Done. Results in evaluation/battery_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
