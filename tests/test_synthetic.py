"""SYNTHETIC_HISTORY_SPEC §6 — modelled pre-inception history.

S1 the financing fit, S2 the era fit, S3 the bill fit, S4 reproducibility and
layout, S5 the XNDX export defect, S6 crash replication, S7 depths of the
bears, S8 bracket inertness, S9 no contamination, S10 QQQ's pre-inception
dividends. Model pins are computed by make_synthetic's own functions, never
read from a generated README; real-data pins run on the committed 2026-08-24
roots.
"""

import datetime as dt
import filecmp
import math
import statistics
from pathlib import Path

import pytest

from main import run_bundle
from make_synthetic import (
    BILL,
    INCEPTION,
    LEVERAGE,
    PUBLISHED,
    RISK,
    aligned,
    bill_levels,
    carry,
    distributions,
    fit_bill,
    fit_drag,
    leveraged_levels,
    main as syn_main,
    read_close,
    spans,
    window,
    yield_by_year,
)
from prices import load_prices
from spec import build_bundle
from test_indicators import SMA_FILES

GOLDEN_DIR = Path(__file__).parent / "data"
GROSS = GOLDEN_DIR / "2026-08-24"
NET = GOLDEN_DIR / "2026-08-24-net15"
SYN = GOLDEN_DIR / "2026-08-24-syn"
SYN_NET = GOLDEN_DIR / "2026-08-24-syn-net15"
W = 0.15

# DTB3's last bar. Every fit stops there: the model has no floating leg past
# it, and a forward-filled tail would quietly bias the constant.
LAST_RATE = "2026-08-20"
RATES = read_close(GROSS / "macro" / "DTB3.csv")

# The roots are committed one commit after the generator (§9), so the byte
# check arms itself rather than blocking the engine commit.
ROOTS = pytest.mark.skipif(
    not (SYN.exists() and SYN_NET.exists()),
    reason="the -syn roots are committed in the following commit (§9)",
)

# §7's cost map: the incumbent lanes' blend map plus BIL at one tick.
COSTS = {"TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6,
         "QQQ": 1, "SPY": 0.7, "BIL": 0.5, "*": 6}
SMA200 = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}


def drag(index: str, fund: str, leverage: int, *, index_root: Path = GROSS,
         fund_root: Path = GROSS, start: str | None = None,
         end: str = LAST_RATE, rates: bool = True) -> dict:
    """A §2.3 fit on the two series' shared calendar. `rates=False` is the
    constant-only variant: the floating leg replaced by zeros."""
    times, index_closes, fund_closes = aligned(
        read_close(index_root / f"{index}.csv"),
        read_close(fund_root / f"{fund}.csv"), start, end,
    )
    y = carry(*RATES, times) if rates else [0.0] * len(times)
    return fit_drag(index_closes, fund_closes, y, spans(times), leverage)


def bill_fit(root: Path, w: float) -> dict:
    """A §2.5 fit of the root's BIL against DTB3 at withholding `w`."""
    times, closes = read_close(root / f"{BILL}.csv")
    at = dict(zip(times, closes))
    kept = window(times, end=LAST_RATE)
    return fit_bill([at[t] for t in kept], carry(*RATES, kept), spans(kept), w)


def log_returns(times: list[str], closes: list[float]) -> dict[str, float]:
    return {
        times[t]: math.log(closes[t] / closes[t - 1]) for t in range(1, len(times))
    }


def correlation(a: list[float], b: list[float]) -> float:
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / math.sqrt(
        sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)
    )


def max_drawdown(at: dict[str, float], times: list[str]) -> float:
    peak, worst = 0.0, 0.0
    for t in times:
        peak = max(peak, at[t])
        worst = min(worst, at[t] / peak - 1.0)
    return worst


def modelled_risk(root: Path, c: float) -> dict[str, float]:
    """The unspliced modelled 3x on the gross index's own calendar."""
    times, closes = read_close(root / "QQQ.csv")
    levels = leveraged_levels(
        closes, carry(*RATES, times), spans(times), LEVERAGE, c
    )
    return dict(zip(times, levels))


def implied_yield(times: list[str], adjusted: list[float], price: list[float]) -> float:
    span = dt.date.fromisoformat(times[-1]) - dt.date.fromisoformat(times[0])
    return -math.log(adjusted[0] / price[0]) / (span.days / 365.25)


def vol_target(safe: str, sigma: float, w_max: float, gate: bool, lam: float = 0.80) -> dict:
    entry = {
        "type": "vol_target", "risk": "TQQQ", "safe": safe, "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": lam}, "leverage": 3,
        "sigma_target": sigma, "w_max": w_max,
    }
    return entry | ({"gate": SMA200} if gate else {})


def bundle(start: str, end: str | None, entries: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "config": {
            "start": start, "end": end, "initial_capital": 10000,
            "monthly_contribution": 500, "cost_bps": COSTS, "cash_yield": 0.03,
        },
        "strategies": entries + [
            {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}}
        ],
    }


def run(spec: dict, data_dir: Path) -> dict[str, dict]:
    return {r.label: r.stats for r in run_bundle(build_bundle(spec), data_dir)}


# --- S1 — the financing fit reproduces, and says why the floating leg exists -


def test_the_financing_fit_reproduces_on_the_full_overlap():
    fit = drag("QQQ", "TQQQ", 3)
    assert fit["n"] == 4155
    assert fit["c"] == pytest.approx(0.01897, abs=0.0001)
    assert fit["beta"] == pytest.approx(2.977, abs=0.003)
    assert fit["residual"] == pytest.approx(0.00177, abs=0.00003)
    assert fit["max_cum_dev"] <= 0.095


@pytest.mark.parametrize(
    "start,end,expected",
    [(None, "2018-06-30", 0.0133), ("2018-07-01", LAST_RATE, 0.0251)],
)
def test_the_financing_constant_halves(start, end, expected):
    assert drag("QQQ", "TQQQ", 3, start=start, end=end)["c"] == pytest.approx(
        expected, abs=0.0002
    )


def test_the_net_root_fits_a_higher_constant_by_its_withheld_distributions():
    # §2.5: a leveraged fund's own distributions are tiny and roughly constant,
    # so the constant absorbs their withholding exactly — the reason the 3x
    # recursion carries no w while the bill's does.
    delta = drag("QQQ", "TQQQ", 3, fund_root=NET)["c"] - drag("QQQ", "TQQQ", 3)["c"]
    times, adjusted = read_close(GROSS / "TQQQ.csv")
    _, price = read_close(GROSS / "price" / "TQQQ.csv")
    assert drag("QQQ", "TQQQ", 3, fund_root=NET)["c"] == pytest.approx(
        0.01943, abs=0.0001
    )
    assert delta == pytest.approx(W * implied_yield(times, adjusted, price), abs=1e-5)


@pytest.mark.parametrize(
    "start,end,expected",
    [(None, "2018-06-30", 0.0193), ("2018-07-01", LAST_RATE, 0.0798)],
)
def test_without_the_floating_leg_the_constant_swings_six_points(start, end, expected):
    # 1.93 vs 7.98 %/yr between the halves, against 1.33 vs 2.51 with DTB3
    # carried: the ZIRP-to-hikes swing is the financing term, not a drag.
    assert drag(
        "QQQ", "TQQQ", 3, start=start, end=end, rates=False
    )["c"] == pytest.approx(expected, abs=0.0002)


# --- S2 — the era fit: a real 2x fund through the GFC and the ZIRP transition


@pytest.mark.parametrize(
    "start,end,expected",
    [(None, "2010-02-10", 0.0241), ("2010-02-11", LAST_RATE, 0.0132)],
)
def test_the_two_times_fund_fits_a_wider_constant_before_2010(start, end, expected):
    assert drag("QQQ", "QLD", 2, start=start, end=end)["c"] == pytest.approx(
        expected, abs=0.0002
    )


@pytest.mark.parametrize("year", range(2006, 2012))
def test_qld_is_stamped_in_step_with_qqq_in_every_year(year):
    # The alignment guard S5's XNDX fails: QLD's larger pre-2010 residual is
    # early-ETF price/NAV noise, not a stamping defect.
    qld_times, qld_closes = read_close(GROSS / "QLD.csv")
    qqq = log_returns(*read_close(GROSS / "QQQ.csv"))
    qld = log_returns(qld_times, qld_closes)
    shared = [t for t in qld if t in qqq and t.startswith(str(year))]
    assert correlation([qqq[t] for t in shared], [qld[t] for t in shared]) >= 0.98


# --- S3 — the bill fit: withholding on an accrual is proportional -----------


def test_the_bill_fit_recovers_the_expense_ratio_on_the_gross_root():
    fit = bill_fit(GROSS, 0.0)
    assert fit["c"] == pytest.approx(0.00109, abs=0.00003)
    assert fit["max_cum_dev"] <= 0.012


def test_the_bill_fit_recovers_the_same_expense_ratio_on_the_net_root():
    fit = bill_fit(NET, W)
    assert fit["c"] == pytest.approx(0.00093, abs=0.00003)
    assert fit["max_cum_dev"] <= 0.012


def test_forcing_a_gross_bill_model_onto_the_net_series_fits_worse():
    # A T-bill fund distributes its whole accrual, so withholding on it scales
    # with the rate and cannot be a constant: the shape test that keeps the
    # proportional term.
    fit = bill_fit(NET, 0.0)
    assert fit["c"] > 0.0030
    assert fit["max_cum_dev"] > 0.02


# --- S4 — reproducibility and layout ----------------------------------------


@pytest.mark.parametrize(
    "parent,root", [(GROSS, SYN), (NET, SYN_NET)], ids=["gross", "net15"]
)
@ROOTS
def test_the_generator_reproduces_the_committed_root_byte_for_byte(parent, root, tmp_path):
    out = tmp_path / "syn"
    syn_main([
        str(parent), "--gross", str(GROSS),
        "--withholding", "0.15" if parent is NET else "0", "--out", str(out),
    ])

    produced = sorted(p.relative_to(out) for p in out.rglob("*") if p.is_file())
    committed = sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file())
    assert produced == committed
    assert len(produced) == 99  # 52 top-level + README + 46 price/ twins
    for rel in committed:
        assert filecmp.cmp(out / rel, root / rel, shallow=False), rel


@pytest.mark.parametrize("symbol", [RISK, BILL])
@pytest.mark.parametrize("root", [SYN, SYN_NET], ids=["gross", "net15"])
@ROOTS
def test_the_source_column_flips_exactly_once_at_the_real_inception(root, symbol):
    header, *rows = (root / f"{symbol}.csv").read_text().splitlines()
    assert header == "time,close,source"
    sources = [row.rsplit(",", 1)[1] for row in rows]
    flips = [i for i in range(1, len(sources)) if sources[i] != sources[i - 1]]
    assert flips == [sources.index("real")]
    assert rows[flips[0]].split(",")[0] == INCEPTION[symbol]


@pytest.mark.parametrize("symbol", [RISK, BILL])
@pytest.mark.parametrize(
    "parent,root", [(GROSS, SYN), (NET, SYN_NET)], ids=["gross", "net15"]
)
@ROOTS
def test_the_real_segment_equals_the_parent_value_for_value(parent, root, symbol):
    parent_times, parent_closes = read_close(parent / f"{symbol}.csv")
    times, closes = read_close(root / f"{symbol}.csv")
    assert times[-len(parent_times):] == parent_times
    assert closes[-len(parent_closes):] == parent_closes


@pytest.mark.parametrize("root", [SYN, SYN_NET], ids=["gross", "net15"])
@ROOTS
def test_the_spliced_symbols_have_no_unadjusted_twin_and_macro_is_not_copied(root):
    for symbol in (RISK, BILL):
        assert not (root / "price" / f"{symbol}.csv").exists()
    assert not (root / "macro").exists()


@pytest.mark.parametrize("root", [SYN, SYN_NET], ids=["gross", "net15"])
@ROOTS
def test_the_loader_reads_the_bear_era_with_no_gaps(root):
    frame = load_prices(root, ["TQQQ", "BIL"], dt.date(2000, 1, 3))
    assert frame["TQQQ"].null_count() == 0
    assert frame["BIL"].null_count() == 0
    assert frame["date"].min() == dt.date(2000, 1, 3)


def test_the_sma_parity_fixture_scope_is_unchanged_by_a_synthetic_root():
    # ROTATION_SPEC §8 T9's count, restated here because a committed -syn root
    # is inside test_indicators' rglob: the spliced files carry `time,close,
    # source` and the 2026-08-24 byte-copies carry no SMA columns, so the
    # collected set must not move.
    assert len(SMA_FILES) == 20


# --- S5 — the XNDX export defect, pinned so a re-export fails loudly --------


@pytest.mark.parametrize("year", [2007, 2008])
def test_xndx_is_stamped_one_day_late_before_2010(year):
    qqq = log_returns(*read_close(GROSS / "QQQ.csv"))
    xndx_times, xndx_closes = read_close(GROSS / "XNDX.csv")
    xndx = log_returns(xndx_times, xndx_closes)
    shared = [t for t in xndx_times if t in qqq and t in xndx]
    dated = [t for t in shared if t.startswith(str(year))]
    following = {a: b for a, b in zip(shared, shared[1:])}
    assert correlation([qqq[t] for t in dated], [xndx[t] for t in dated]) < 0.2
    lead = [t for t in dated if t in following]
    assert correlation(
        [qqq[t] for t in lead], [xndx[following[t]] for t in lead]
    ) > 0.95


@pytest.mark.parametrize("year", range(2010, 2026))
def test_xndx_is_stamped_correctly_from_2010(year):
    qqq = log_returns(*read_close(GROSS / "QQQ.csv"))
    xndx = log_returns(*read_close(GROSS / "XNDX.csv"))
    dated = [t for t in xndx if t in qqq and t.startswith(str(year))]
    assert correlation([qqq[t] for t in dated], [xndx[t] for t in dated]) >= 0.99


# --- S6 — crash replication: the model against the fund it was fitted on -----


@pytest.mark.parametrize(
    "start,end,tolerance",
    [("2020-02-01", "2020-04-30", 0.005), ("2021-11-01", "2023-01-31", 0.005),
     ("2018-08-01", "2018-12-31", 0.005), ("2025-02-01", "2025-05-31", 0.005)],
)
def test_the_model_reproduces_every_crash_the_overlap_contains(start, end, tolerance):
    modelled = modelled_risk(GROSS, drag("QQQ", "TQQQ", 3)["c"])
    times, closes = read_close(GROSS / "TQQQ.csv")
    real = dict(zip(times, closes))
    kept = window(times, start, end)
    assert max_drawdown(modelled, kept) == pytest.approx(
        max_drawdown(real, kept), abs=tolerance
    )


def test_the_cumulative_ratio_never_wanders_far_over_the_overlap():
    modelled = modelled_risk(GROSS, drag("QQQ", "TQQQ", 3)["c"])
    times, closes = read_close(GROSS / "TQQQ.csv")
    shared = [t for t in times if t in modelled]
    ratio = [closes[times.index(t)] / modelled[t] for t in shared]
    normalised = [r / ratio[0] for r in ratio]
    assert 0.98 <= min(normalised) and max(normalised) <= 1.11


# --- S7 — depths of the bears the data never had ----------------------------


@pytest.mark.parametrize(
    "start,end,ceiling,index_depth",
    [("2000-03-01", "2003-03-31", -0.999, -0.8298),
     ("2007-10-01", "2009-03-31", -0.94, -0.534)],
)
@ROOTS
def test_the_modelled_fund_is_annihilated_in_both_bears(start, end, ceiling, index_depth):
    times, closes = read_close(SYN / f"{RISK}.csv")
    kept = window(times, start, end)
    assert max_drawdown(dict(zip(times, closes)), kept) <= ceiling
    index_times, index_closes = read_close(GROSS / "QQQ.csv")
    assert max_drawdown(
        dict(zip(index_times, index_closes)), window(index_times, start, end)
    ) == pytest.approx(index_depth, abs=0.001)


# --- S8 — bracket inertness: the machine's verdict does not ride on `c` ------


@pytest.mark.parametrize("c", [0.0129, 0.0413], ids=["c_lo", "c_hi"])
@ROOTS
def test_the_drag_bracket_moves_the_gated_machine_barely(c, tmp_path):
    out = tmp_path / "bracket"
    syn_main([str(NET), "--gross", str(GROSS), "--withholding", "0.15",
              "--drag", str(c), "--out", str(out)])
    spec = bundle("2000-01-03", "2011-12-30", [vol_target("BIL", 0.20, 0.8, True)])
    arm = next(k for k in run(spec, SYN_NET) if k.startswith("VT"))
    committed, bracket = run(spec, SYN_NET)[arm], run(spec, out)[arm]
    assert bracket["cagr"] == pytest.approx(committed["cagr"], abs=0.007)
    assert bracket["max_drawdown"] == pytest.approx(
        committed["max_drawdown"], abs=0.005
    )


# --- S9 — no contamination: a 2012 run reads only real bars -----------------


@ROOTS
def test_the_2012_composition_anchor_survives_the_synthetic_root_bit_for_bit():
    spec = bundle("2012-01-03", None, [
        vol_target("BTAL", 0.30, 0.6, True), vol_target("BTAL", 0.30, 0.6, False),
    ])
    stats = run(spec, SYN_NET)
    gated = stats["VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200"]
    assert round(gated["calmar"], 8) == 0.86123626
    assert round(gated["cagr"], 8) == 0.23817105  # §9 quotes it to 7 dp
    assert round(gated["max_drawdown"], 8) == -0.27654555
    ungated = stats["VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80"]
    assert round(ungated["calmar"], 8) == 0.71623794


# --- S10 — QQQ's pre-inception dividends, checked by structure --------------


def test_the_dot_com_stretch_carries_no_dividends_at_all():
    times, adjusted = read_close(GROSS / "QQQ.csv")
    _, price = read_close(GROSS / "price" / "QQQ.csv")
    implied = distributions(times, adjusted, price)
    pre = [date for date, _ in implied if date <= "2010-12-31"]
    assert len(pre) == 24
    assert pre[0] == "2003-12-24"


@pytest.mark.parametrize(
    "year,expected",
    [(2003, 0.04), (2004, 0.95), (2005, 0.33), (2006, 0.32),
     (2007, 0.30), (2008, 0.36), (2009, 0.56), (2010, 0.73)],
)
def test_the_implied_yield_by_year_is_small_enough_to_be_harmless(year, expected):
    # Even if every one of these were wrong, 0.95 %/yr is at most ~2.9 %/yr of
    # 3x exposure — inside the §2.4 drag bracket.
    times, adjusted = read_close(GROSS / "QQQ.csv")
    _, price = read_close(GROSS / "price" / "QQQ.csv")
    yields = yield_by_year(times, price, distributions(times, adjusted, price))
    assert 100 * yields[year] == pytest.approx(expected, abs=0.005)


def test_the_implied_distributions_match_the_issuers_published_record():
    times, adjusted = read_close(GROSS / "QQQ.csv")
    _, price = read_close(GROSS / "price" / "QQQ.csv")
    implied = dict(distributions(times, adjusted, price))
    assert PUBLISHED, "the operator spot check needs at least one published amount"
    for date, published in PUBLISHED.items():
        assert implied[date] == pytest.approx(published, abs=0.0005), date
