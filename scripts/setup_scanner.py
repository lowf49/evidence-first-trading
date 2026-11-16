"""Scan the most recent session for Tier-A/B setup triggers (never predicts).

Usage: python setup_scanner.py --symbols SPY,QQQ,NVDA
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D  # noqa: E402

CATALOG_NOTE = ("grades from references/setup-catalog.md: A1 ORB [Tier A], "
                "A2 PDH/PDL [Tier A levels / Tier B entry]")


def scan(sym):
    bars = D.sessions(D.fetch_bars(sym, "5m", "10d"))
    keys = sorted(bars)
    if len(keys) < 2:
        return [f"{sym}: insufficient data"]
    today, prev = bars[keys[-1]], bars[keys[-2]]
    prev_hi = max(b["h"] for b in prev)
    prev_lo = min(b["l"] for b in prev)
    prev_close = prev[-1]["c"]
    out = []

    or_bars = [b for b in today if D.minutes_since_open(b) < 15]
    trig = next((b for b in today if D.minutes_since_open(b) == 15), None)
    last = today[-1]
    if len(or_bars) >= 3 and trig:
        or_hi = max(b["h"] for b in or_bars)
        or_lo = min(b["l"] for b in or_bars)
        if trig["c"] > or_hi:
            out.append(f"{sym}: A1 ORB LONG trigger fired @ {trig['c']:.2f} "
                       f"(OR high {or_hi:.2f}) [Tier A]")
        elif trig["c"] < or_lo:
            out.append(f"{sym}: A1 ORB SHORT trigger fired @ {trig['c']:.2f} "
                       f"(OR low {or_lo:.2f}) [Tier A]")
        else:
            out.append(f"{sym}: A1 no trigger (price inside OR {or_lo:.2f}-{or_hi:.2f})")
    d = last["c"]
    pdh_dist = (prev_hi - d) / d * 100
    pdl_dist = (prev_lo - d) / d * 100
    if abs(pdh_dist) <= 0.10:
        out.append(f"{sym}: A2 price AT prior-day-high ({prev_hi:.2f}, {pdh_dist:+.3f}%) "
                   "[Tier A level; entry Tier B]")
    elif abs(pdl_dist) <= 0.10:
        out.append(f"{sym}: A2 price AT prior-day-low ({prev_lo:.2f}, {pdl_dist:+.3f}%) "
                   "[Tier A level; entry Tier B]")
    else:
        out.append(f"{sym}: A2 levels: PDH {prev_hi:.2f} ({pdh_dist:+.2f}%), "
                   f"PDL {prev_lo:.2f} ({pdl_dist:+.2f}%) - not near")
    # U-shape context (descriptive only)
    out.append(f"{sym}: context: session last bar {last['local']:%H:%M} ET, "
               f"prev close {prev_close:.2f}")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True)
    a = p.parse_args()
    print(f"Setup scan - {CATALOG_NOTE}")
    print("Output = trigger status only; no direction is predicted.\n")
    for sym in [s.strip().upper() for s in a.symbols.split(",") if s.strip()]:
        try:
            for line in scan(sym):
                print(line)
        except Exception as e:
            print(f"{sym}: ERROR {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
