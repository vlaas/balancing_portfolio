"""Named, causal indicators computed from one symbol's own close series."""

import math
from collections.abc import Callable
from dataclasses import dataclass

import polars as pl

TRADING_DAYS = 252


@dataclass(frozen=True)
class Indicator:
    """A named, causal function of one symbol's close series.

    `fn` receives the symbol's own frame with columns `date` (ascending, unique)
    and `close` (Float64, non-null) and returns a Float64 Series of the same
    length, null during warm-up. `name` is the column suffix and the identity:
    two Indicators with the same name are the same indicator.

    When `inputs` is not empty, `fn` instead receives the frame restricted to
    the intersection of the host's and every input's calendars, with one extra
    Float64 column per input symbol (REGIME_SPEC §3.1); the loader carries the
    result back onto the host's own rows by date, null outside the intersection.
    """

    name: str
    fn: Callable[[pl.DataFrame], pl.Series]
    inputs: tuple[str, ...] = ()


def _log_returns(frame: pl.DataFrame) -> pl.Series:
    """Daily log returns; null on the first row, which has no previous close."""
    return (frame["close"] / frame["close"].shift(1)).log()


def sma(n: int) -> Indicator:
    """Arithmetic mean of the last `n` closes, today's included."""
    return Indicator(f"SMA{n}", lambda frame: frame["close"].rolling_mean(n))


def sma_monthly(m: int) -> Indicator:
    """Mean of the last `m` month-end closes, carried forward between month-ends.

    A row is a month-end iff its month differs from the next row's — the same
    rule as `is_rebalance_day`, so the value on a rebalance day includes that
    day's close and the file's final (partial-month) row is never a month-end.
    """

    def fn(frame: pl.DataFrame) -> pl.Series:
        month_end = (
            pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month()
        ).fill_null(False)
        month_ends = frame.filter(month_end).select(
            "date", value=pl.col("close").rolling_mean(m)
        )
        return frame.join_asof(month_ends, on="date", strategy="backward")["value"]

    return Indicator(f"SMA{m}M", fn)


def realized_vol(n: int) -> Indicator:
    """Annualised sample standard deviation of the last `n` log returns."""
    return Indicator(
        f"VOL{n}",
        lambda frame: _log_returns(frame).rolling_std(n, ddof=1)
        * math.sqrt(TRADING_DAYS),
    )


def ewma_vol(lam: float = 0.94) -> Indicator:
    """Annualised RiskMetrics EWMA volatility: zero-mean, no bias correction.

    Null for the first 20 rows, so estimates still dominated by the seed
    (`s²_1 = r_1²`) are never read by a strategy.
    """

    def fn(frame: pl.DataFrame) -> pl.Series:
        variance = (_log_returns(frame) ** 2).ewm_mean(
            alpha=1 - lam, adjust=False, min_samples=20
        )
        return (variance * TRADING_DAYS).sqrt()

    return Indicator(f"VOL_EWMA{round(lam * 100)}", fn)


def drawdown() -> Indicator:
    """Fraction below the running maximum close over the file's whole history."""
    return Indicator("DD", lambda frame: frame["close"] / frame["close"].cum_max() - 1)


def momentum(n: int) -> Indicator:
    """Total return over the last `n` bars."""
    return Indicator(f"MOM{n}", lambda frame: frame["close"] / frame["close"].shift(n) - 1)


def _month_end_values(frame: pl.DataFrame, value: pl.Expr) -> pl.Series:
    """`value` evaluated over the month-end rows, carried forward between them.

    The `sma_monthly` rule: a row is a month-end iff its month differs from
    the next row's, on the symbol's own bar calendar, so the value on a
    month-end row includes that day's close and the file's final
    (partial-month) row is never a month-end.
    """
    month_end = (
        pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month()
    ).fill_null(False)
    month_ends = frame.filter(month_end).select("date", value=value)
    return frame.join_asof(month_ends, on="date", strategy="backward")["value"]


def mom_monthly(k: int) -> Indicator:
    """Total return over the last `k` month-ends of the symbol's own calendar.

    At month-end t: `close_t / close_{t-k month-ends} - 1`, carried forward;
    null until k+1 month-ends exist (ROTATION_SPEC §4.1).
    """
    assert k >= 1, f"mom_monthly: k must be >= 1, got {k}"
    return Indicator(
        f"MOM{k}M",
        lambda frame: _month_end_values(
            frame, pl.col("close") / pl.col("close").shift(k) - 1
        ),
    )


def mom_multi(months: tuple[int, ...], weights: tuple[float, ...] | None = None) -> Indicator:
    """Weighted combination of month-end total returns over several horizons.

    `sum_i w_i * (close_t / close_{t-m_i} - 1)` over month-end closes, the
    unweighted mean when `weights` is None; null until max(months)+1
    month-ends exist (ROTATION_SPEC §4.2). Ranking and sign are invariant to
    positive scaling, so Keller's published /4 normalisations differ by a
    constant factor only: 13612W is `mom_multi((1, 3, 6, 12), (12, 4, 2, 1))`,
    13612U is `mom_multi((1, 3, 6, 12))`.
    """
    months = tuple(months)
    assert months, f"mom_multi: months must be non-empty, got {months}"
    assert all(m >= 1 for m in months), f"mom_multi: months must be >= 1, got {months}"
    assert all(a < b for a, b in zip(months, months[1:])), (
        f"mom_multi: months must be strictly ascending, got {months}"
    )
    if weights is None:
        applied = tuple(1.0 / len(months) for _ in months)
        suffix = "U"
    else:
        assert len(weights) == len(months), (
            f"mom_multi: months and weights must have equal length, "
            f"got {months} / {tuple(weights)}"
        )
        assert all(w > 0 for w in weights), (
            f"mom_multi: weights must be > 0, got {tuple(weights)}"
        )
        applied = tuple(float(w) for w in weights)
        suffix = "W" + "-".join(f"{w:g}" for w in applied)

    def value() -> pl.Expr:
        close = pl.col("close")
        terms = [w * (close / close.shift(m) - 1) for m, w in zip(months, applied)]
        total = terms[0]
        for term in terms[1:]:
            total = total + term  # `+` propagates nulls, unlike sum_horizontal
        return total

    return Indicator(
        "MOMM" + "-".join(str(m) for m in months) + suffix,
        lambda frame: _month_end_values(frame, value()),
    )


def sma_gap(m: int) -> Indicator:
    """Gap of the month-end close above its own `sma_monthly(m)` value.

    `close_t / SMA_mM(t) - 1` at month-ends, carried forward; reuses the
    `sma_monthly(m)` window (m month-end closes, today's included). Faber's
    10-month filter is the sign of `sma_gap(10)` (ROTATION_SPEC §4.3).
    """
    assert m >= 2, f"sma_gap: m must be >= 2, got {m}"
    return Indicator(
        f"SMAGAP{m}M",
        lambda frame: _month_end_values(
            frame, pl.col("close") / pl.col("close").rolling_mean(m) - 1
        ),
    )


def ratio_sma(denominator: str, n: int) -> Indicator:
    """Mean of the last `n` values of close / `denominator`, on joint days only.

    `n = 1` is the raw ratio. The window counts joint trading days: a host day
    the denominator lacks never enters it (REGIME_SPEC §3.1).
    """
    assert n >= 1, f"ratio_sma: n must be >= 1, got {n}"
    return Indicator(
        f"RATIO_{denominator}_SMA{n}",
        lambda frame: (frame["close"] / frame[denominator]).rolling_mean(n),
        inputs=(denominator,),
    )


def _pct_steps(name: str, value: float) -> int:
    """`value` as a count of 0.01 steps; asserted exact so names are lossless."""
    steps = round(value * 100)
    assert value >= 0 and abs(value * 100 - steps) < 1e-9, (
        f"ts_regime: {name} must be a non-negative multiple of 0.01, got {value}"
    )
    return steps


def ts_regime(denominator: str, n: int, fire: float, hysteresis: float = 0.0) -> Indicator:
    """Hysteresis risk-off state of the smoothed close / `denominator` ratio.

    With `s` the `ratio_sma(denominator, n)` series (REGIME_SPEC §3.5): null
    during warm-up; on the first value, off iff `s >= fire`; then fires at
    `s >= fire` and releases below `fire - hysteresis`, else holds its state.
    1.0 while off, 0.0 while on; with `hysteresis = 0` this collapses exactly
    to `s >= fire`. Runs daily on the signal's own joint calendar; a strategy
    reads it on rebalance days only.
    """
    fire_steps = _pct_steps("fire", fire)
    hysteresis_steps = _pct_steps("hysteresis", hysteresis)
    assert hysteresis < fire, (
        f"ts_regime: hysteresis {hysteresis} must be below fire {fire}"
    )
    smooth = ratio_sma(denominator, n)
    release = fire - hysteresis

    def fn(frame: pl.DataFrame) -> pl.Series:
        out: list[float | None] = []
        off: bool | None = None
        for s in smooth.fn(frame):
            if s is None:
                out.append(None)
                continue
            if off is None or (not off and s >= fire):
                off = s >= fire
            elif off and s < release:
                off = False
            out.append(1.0 if off else 0.0)
        return pl.Series(out, dtype=pl.Float64)

    return Indicator(
        f"REGIME_{denominator}_{n}_{fire_steps}_{hysteresis_steps}",
        fn,
        inputs=(denominator,),
    )
