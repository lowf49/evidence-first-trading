"""SQLite trade journal with honest post-hoc stats (Wilson CI, R distribution, skew).

Usage:
  python journal.py add --symbol SPY --dir LONG --entry 670.1 --stop 668.9 --exit 671.5 --tier A1
  python journal.py summary
"""
import argparse
import math
import os
import sqlite3
import sys
import time

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "journal.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
  id INTEGER PRIMARY KEY,
  ts INTEGER, symbol TEXT, direction TEXT, tier TEXT,
  entry REAL, stop REAL, exit REAL, r REAL, cost REAL,
  planned_wr REAL, notes TEXT
);
"""


def wilson(wr, n, z=1.96):
    if n <= 0:
        return (0.0, 1.0)
    d = 1 + z * z / n
    c = wr + z * z / (2 * n)
    m = z * math.sqrt(wr * (1 - wr) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--symbol", required=True)
    a.add_argument("--dir", required=True, choices=["LONG", "SHORT"])
    a.add_argument("--tier", required=True)
    a.add_argument("--entry", type=float, required=True)
    a.add_argument("--stop", type=float, required=True)
    a.add_argument("--exit", type=float, required=True)
    a.add_argument("--cost", type=float, default=0.0, help="round-trip $ cost")
    a.add_argument("--planned-wr", type=float, default=None)
    a.add_argument("--notes", default="")
    sub.add_parser("summary")
    args = p.parse_args()

    con = sqlite3.connect(DB)
    con.execute(SCHEMA)

    if args.cmd == "add":
        risk = abs(args.entry - args.stop)
        if risk <= 0:
            print("REFUSED: stop == entry (zero risk definition)")
            return 2
        raw = (args.exit - args.entry) * (1 if args.dir == "LONG" else -1)
        r = raw / risk - (args.cost / risk if args.cost else 0)
        con.execute(
            "INSERT INTO trades (ts,symbol,direction,tier,entry,stop,exit,r,cost,planned_wr,notes)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (int(time.time()), args.symbol, args.dir, args.tier,
             args.entry, args.stop, args.exit, r, args.cost,
             args.planned_wr, args.notes))
        con.commit()
        print(f"added: {args.symbol} {args.dir} {args.tier} -> {r:+.2f}R")
        return 0

    rows = con.execute("SELECT r, planned_wr FROM trades").fetchall()
    n = len(rows)
    if n == 0:
        print("no trades")
        return 0
    wins = [r for r, _ in rows if r > 0]
    wr = len(wins) / n
    rs = [r for r, _ in rows]
    lo, hi = wilson(wr, n)
    expectancy = sum(rs) / n
    # longest losing streak
    streak = cur = 0
    for r in rs:
        cur = cur + 1 if r <= 0 else 0
        streak = max(streak, cur)
    avg_win = sum(w for w in wins) / len(wins) if wins else 0
    losses = [-r for r in rs if r <= 0]
    avg_loss = sum(losses) / len(losses) if losses else 0
    planned = [pw for _, pw in rows if pw is not None]

    print(f"trades           : {n}")
    print(f"win rate         : {wr:.1%}  (95% Wilson CI [{lo:.1%}, {hi:.1%}])")
    print(f"expectancy       : {expectancy:+.3f} R/trade")
    print(f"avg win / loss   : {avg_win:.2f}R / {avg_loss:.2f}R")
    print(f"longest loss str.: {streak}")
    if planned:
        pw = sum(planned) / len(planned)
        print(f"planned vs actual: {pw:.1%} vs {wr:.1%}  "
              f"({'overconfident' if pw > wr + 0.05 else 'aligned' if abs(pw - wr) <= 0.05 else 'underconfident'})")
    if wr >= 0.7 and avg_loss > 2 * avg_win:
        print("SKEW WARNING: steamroller profile (many small wins, rare large loss).")
    if n < 30:
        print("SAMPLE GATE: REJECT (<30)")
    elif n < 200:
        print("SAMPLE GATE: WARN (30-199)")
    else:
        print("SAMPLE GATE: PASS (>=200)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
