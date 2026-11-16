"""Cost breakeven table by market - at what gross target does the math work?

Usage:
  python cost_breakeven.py --target-pct 0.4 --wr 0.55 --winR 1.2
  python cost_breakeven.py --list
"""
import argparse
import sys

# Round-trip cost as fraction of notional. Order-of-magnitude defaults; VERIFY with
# your own fills (cite cost-math.md). maker = passive limit orders, taker = aggressive.
MARKETS = {
    "us_stock_commission_free": {"rt": 0.0008, "note": "spread ~0.05-0.1% implicit; PDT rule <25k"},
    "us_stock_pdt":             {"rt": 0.0008, "note": "max 3 day-trades / 5 sessions under $25k"},
    "es_futures":               {"rt": 0.0005, "note": "1 tick=0.25pt=$12.50; commissions ~$1.25-2.40/side"},
    "nq_futures":               {"rt": 0.0006, "note": "1 tick=0.25pt=$5.00; wider ranges"},
    "fx_retail":                {"rt": 0.0004, "note": "2-5 pips + commission"},
    "crypto_spot_taker":        {"rt": 0.0016, "note": "0.08-0.2% RT taker fees"},
    "crypto_spot_maker":        {"rt": 0.0004, "note": "0.02% RT or 0 with rebate tiers"},
    "crypto_perp_maker":        {"rt": 0.0002, "note": "maker rebates on some venues = only structural retail niche"},
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--list", action="store_true", help="print market cost table")
    p.add_argument("--target-pct", type=float, default=None, help="gross target, %% of notional, round trip")
    p.add_argument("--wr", type=float, default=None)
    p.add_argument("--winR", type=float, default=None)
    a = p.parse_args()

    if a.list or (a.target_pct is None):
        print(f"{'market':28s} {'RT cost %':>10s}  note")
        for k, v in MARKETS.items():
            print(f"{k:28s} {v['rt']*100:9.3f}%  {v['note']}")
        print("\nSweep slippage 0/5/10/20/50bp on ANY backtest. Edge dying at 10bp = no edge.")
        return 0

    print(f"{'market':28s} {'cost %':>8s} {'kept of target':>15s} {'breakeven target':>17s}")
    for k, v in MARKETS.items():
        cost = v["rt"] * 100
        kept = (a.target_pct - cost) / a.target_pct * 100 if a.target_pct else 0
        # target needed so net = 50% of gross target
        be = cost / 0.5
        flag = "" if kept >= 50 else "  <-- FAILS 50% keep-rate"
        print(f"{k:28s} {cost:7.3f}% {kept:14.1f}% {be:16.3f}%{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
