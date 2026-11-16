"""Net expectancy calculator. REFUSES to run without cost inputs.

Usage:
  python expectancy_calc.py --wr 0.55 --winR 1.2 --lossR 1.0 --costR 0.15
  python expectancy_calc.py --wr 0.55 --winR 1.2 --lossR 1.0 --costR 0.15 --n 120
"""
import argparse
import math
import sys


def wilson(wr: float, n: int, z: float = 1.96) -> tuple:
    if n <= 0:
        return (0.0, 1.0)
    d = 1 + z * z / n
    c = wr + z * z / (2 * n)
    m = z * math.sqrt(wr * (1 - wr) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--wr", type=float, required=True, help="win rate 0..1")
    p.add_argument("--winR", type=float, required=True, help="avg win in R")
    p.add_argument("--lossR", type=float, required=True, help="avg loss in R (positive)")
    p.add_argument("--costR", type=float, default=None,
                   help="ROUND-TRIP cost in R (commission+spread+slippage). REQUIRED.")
    p.add_argument("--n", type=int, default=None,
                   help="sample size of historical occurrences (for Wilson interval)")
    a = p.parse_args()

    if a.costR is None:
        print("REFUSED: --costR is required. An expectancy without costs is not an "
              "expectancy (Barber et al. 2009: 3.8pp/yr retail drag). Estimate it with "
              "scripts/cost_breakeven.py and a slippage sweep of 0/5/10/20/50bp.")
        return 2
    if not (0 <= a.wr <= 1) or a.lossR <= 0:
        print("REFUSED: wr must be in [0,1], lossR > 0.")
        return 2

    gross = a.wr * a.winR - (1 - a.wr) * a.lossR
    net = gross - a.costR
    be = 1 / (1 + a.winR / a.lossR)

    print(f"Expectancy gross : {gross:+.4f} R/trade")
    print(f"Round-trip cost  : {a.costR:.4f} R/trade")
    print(f"Expectancy NET   : {net:+.4f} R/trade")
    print(f"Breakeven WR at {a.winR / a.lossR:.2f}:R : {be:.1%}")
    print(f"Verdict          : {'POSITIVE net (still fragile - see failure-modes)' if net > 0 else 'NEGATIVE net'}")

    if a.n is not None:
        lo, hi = wilson(a.wr, a.n)
        print(f"WR 95% Wilson CI : [{lo:.1%}, {hi:.1%}] (n={a.n})")
        if a.n < 30:
            print("SAMPLE GATE: REJECT (<30 occurrences)")
            return 3
        if a.n < 200:
            print("SAMPLE GATE: WARN (30-199; needs 200-500 across regimes for confidence)")
        else:
            print("SAMPLE GATE: PASS (>=200)")
    # negative-skew flag
    if a.wr >= 0.7 and a.lossR >= 2 * a.winR:
        print("SKEW WARNING: high-WR with loss > 2x win = steamroller profile "
              "(one gap/lock can erase dozens of wins).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
