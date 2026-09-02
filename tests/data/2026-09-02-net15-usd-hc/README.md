# Haircut snapshot — 2026-09-02-net15-usd-hc

Derived from the frozen `2026-09-02-net15-usd` snapshot by `make_haircut.py`
(EU_SUBSTITUTE_SPEC §6.3): each carried US symbol's close is compounded
down by h/252 per bar from its first bar in the root — formula
`close_t × (1 − h/100/252)^k`, k bars since the first — so a haircut
lane measures the translation cost of a substitutable component on the
winner's own window. A haircut `<SYM>.csv` carries `time,close` only and
has no `price/` twin — a modelled series has no unadjusted twin. A
symbol with h = 0 is byte-copied (the no-contamination invariant holds
by construction). Unsubstitutable slots (KMLM, BTAL) are absent from
the map by design and take no fictitious haircut; their columns are
flagged translation-incomplete in the verdict. Every other file,
`price/` twins included, is byte-copied from the parent.

| symbol | h %/yr | bars | final factor |
|---|---|---|---|
| BIL | 0 | — | byte-copied |
| TQQQ | 0.142064 | 4165 | 0.9767989371103649 |
