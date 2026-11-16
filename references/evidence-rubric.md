# Evidence rubric — how a setup gets its tier

## Requirements (all must hold for the tier above it)

| Requirement | C | B | A |
|---|---|---|---|
| Precise, implementable trigger rules (no "look for confluence") | ✔ | ✔ | ✔ |
| Independent replication (someone other than the author tested it) | — | ✔ | ✔ |
| Explicit sample size (n trades or n sessions) + date range | claimed | ✔ | ✔ |
| Net-of-cost reporting OR cost inputs available to re-derive | — | required | required |
| Peer-reviewed publication | — | — | ✔ |
| Survives data-snooping controls (Reality Check/SPA/DSR) or pre-registered | — | — | ✔ *or* noted limitation |

## Automatic downgrades
- **Repainting or same-bar look-ahead in the implementation → D** (backtest invalid; see failure-modes §1).
- **Undisclosed trial count during optimization → B at best**, flagged.
- **Win rate published without n → C** (cannot assess).
- **Only author/vendor reports exist → C**, "vendor-claimed".
- **Tested and failed after costs → D**.

## Upgrade path
C → B: independent backtest with published n, date range, and cost assumptions.
B → A: peer-reviewed publication (or top-tier working paper) + independent replication + snooping controls.

## Reporting language rules
- Allowed: "historically occurred X% of sessions (n=…, date range, source)"; "no published evidence found"; "backtested with costs, fragile at 10bp".
- Banned: "guaranteed", "will", "high-probability" without n, "reliable" without source, any future-tense price statement.

## Default
**Unknown setup = Tier C (LORE).** Absence of evidence is not evidence of absence — but it is not permission to treat a setup as validated either.
