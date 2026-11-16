"""Keyless Yahoo Finance data layer (stdlib only)."""
import json
import urllib.request
import datetime as dt

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) evidence-first-trading"}


def fetch_bars(symbol: str, interval: str = "5m", range_: str = "60d") -> list:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={range_}&interval={interval}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    res = data["chart"]["result"][0]
    ts = res.get("timestamp") or []
    q = res["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        bars.append({"dt": t, "o": o, "h": h, "l": l, "c": c,
                     "v": q["volume"][i] or 0})
    return bars


def et(epoch: int) -> dt.datetime:
    """US/Eastern conversion with correct 2026 DST rules (Mar 8 - Nov 1)."""
    u = dt.datetime.fromtimestamp(epoch, dt.timezone.utc)
    if dt.date(u.year, 3, 8) <= u.date() < dt.date(u.year, 11, 1):
        off = dt.timedelta(hours=-4)
    else:
        off = dt.timedelta(hours=-5)
    return dt.datetime.fromtimestamp(epoch, dt.timezone(off))


def sessions(bars: list) -> dict:
    """Group bars by ET session date; keep 09:30-16:00 regular hours only."""
    out = {}
    for b in bars:
        d = et(b["dt"])
        tod = d.hour * 60 + d.minute
        if not (9 * 60 + 30 <= tod < 16 * 60):
            continue
        b["local"] = d
        out.setdefault(d.date().isoformat(), []).append(b)
    return {k: sorted(v, key=lambda x: x["dt"]) for k, v in sorted(out.items())}


def minutes_since_open(b: dict) -> int:
    d = b["local"]
    return d.hour * 60 + d.minute - (9 * 60 + 30)
